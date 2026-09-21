"""
BLE-Empfaenger fuer den Pybricks Spike Prime Hub.

Verbindet sich ueber Bluetooth Low Energy (Nordic UART Service)
mit dem Hub und empfaengt die print()-Ausgaben des Brick-Programms.
Laeuft in einem eigenen QThread, um den UI-Thread nicht zu blockieren.
"""

import asyncio
import sys
from bleak import BleakClient, BleakScanner
from PySide6.QtCore import QThread, Signal, QObject


# Nordic UART Service UUIDs
NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # Schreiben → Hub
NUS_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # Lesen ← Hub

# Pybricks-spezifische UUIDs (falls NUS nicht funktioniert)
PYBRICKS_SERVICE_UUID = "C5F50001-8280-46DA-89F4-6D8051E4AEEF"
PYBRICKS_CHAR_UUID = "C5F50002-8280-46DA-89F4-6D8051E4AEEF"


class BLEReceiver(QThread):
    """BLE-Empfaenger der in einem separaten Thread laeuft.

    Signale:
        verbunden(bool): Hub-Verbindungsstatus geaendert.
        nachricht(str): Rohe Textnachricht vom Hub empfangen.
        fehler(str): Fehlermeldung bei Verbindungsproblemen.
    """

    verbunden = Signal(bool)
    nachricht = Signal(str)
    fehler = Signal(str)
    hubNameGeaendert = Signal(str)
    debugNachricht = Signal(str)

    def __init__(self, hub_name="Pybricks Hub", parent=None):
        super().__init__(parent)
        self._hub_name = hub_name
        self._running = True
        self._client = None
        self._empfangs_puffer = ""

    def _handle_disconnect(self, client):
        """Wird aufgerufen, wenn die BLE-Verbindung abbricht."""
        print("!!! BLE VERBINDUNG GETRENNT (DISCONNECT EVENT) !!!")
        self.verbunden.emit(False)

    def stop(self):
        """Beendet den BLE-Thread sauber."""
        self._running = False

    def run(self):
        """Threadstart – erstellt einen neuen asyncio-Event-Loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._ble_hauptschleife())
        except Exception as e:
            self.fehler.emit(f"BLE-Fehler: {e}")
        finally:
            loop.close()

    async def _ble_hauptschleife(self):
        """Hauptschleife: sucht Hub, verbindet und empfaengt Daten."""
        while self._running:
            try:
                self.fehler.emit("Suche Pybricks Hub...")

                # Hub suchen
                device = await BleakScanner.find_device_by_name(
                    self._hub_name, timeout=10.0
                )

                if device is None:
                    # Alternativ: Nach jedem Geraet mit Pybricks-Service suchen
                    device = await BleakScanner.find_device_by_filter(
                        lambda d, ad: (
                            PYBRICKS_SERVICE_UUID.lower()
                            in [str(u).lower() for u in (ad.service_uuids or [])]
                        ),
                        timeout=10.0,
                    )

                if device is None:
                    self.fehler.emit("Hub nicht gefunden. Neuer Versuch...")
                    await asyncio.sleep(2)
                    continue

                self.fehler.emit(f"Verbinde mit {device.name}...")

                async with BleakClient(
                    device,
                    timeout=15.0,
                    disconnected_callback=self._handle_disconnect,
                ) as client:
                    print("!!! BLE VERBUNDEN - WARTE AUF NOTIFICATIONS !!!")
                    self.debugNachricht.emit("BLE VERBUNDEN")
                    self._client = client
                    self.verbunden.emit(True)
                    self.hubNameGeaendert.emit(device.name or "Unbekannter Hub")
                    self.fehler.emit("")

                    # Versuche alle verfuegbaren Notifications zu abonnieren (Diagnose-Modus)
                    abonnierte_anzahl = 0
                    for service in client.services:
                        for char in service.characteristics:
                            if "notify" in char.properties:
                                try:
                                    def create_handler(uuid_str):
                                        def handler(sender, data: bytearray):
                                            print(f"[{uuid_str}] {data}")
                                            # Leite trotzdem an unseren Haupt-Handler weiter
                                            self._notification_handler(sender, data)
                                        return handler
                                    
                                    await client.start_notify(char.uuid, create_handler(char.uuid))
                                    abonnierte_anzahl += 1
                                    print(f"Abonniert auf: {char.uuid}")
                                except Exception as e:
                                    print(f"Fehler beim Abonnieren von {char.uuid}: {e}")

                    if abonnierte_anzahl > 0:
                        self.debugNachricht.emit(f"{abonnierte_anzahl} Kanäle aktiv")
                    else:
                        self.debugNachricht.emit("KEINE Notify-Kanäle gefunden!")
                        self.fehler.emit(
                            "Kein kompatibler BLE-Service gefunden!"
                        )
                        continue

                    # Verbindung halten
                    while self._running and client.is_connected:
                        await asyncio.sleep(0.5)

                    self.verbunden.emit(False)
                    self.hubNameGeaendert.emit("")
                    self._client = None

            except Exception as e:
                self.verbunden.emit(False)
                self.hubNameGeaendert.emit("")
                self._client = None
                self.fehler.emit(f"Verbindungsfehler: {e}")
                await asyncio.sleep(3)

    def _notification_handler(self, sender, data: bytearray):
        """Verarbeitet eingehende BLE-Notifications."""
        print(f"[BLE RAW DATEN] Sender: {sender}, Data: {data}")
        self.debugNachricht.emit(f"RAW: {data.hex()}")
        try:
            if not data:
                return

            # Pybricks Protocol: 
            # 0x01 is stdout, 0x02 is stderr
            # 0x00 is Status Report (battery, etc), which we MUST ignore!
            if data[0] in (1, 2):
                data = data[1:]
            elif data[0] < 32:
                # Binaere Steuer-Pakete (z.B. Status) ignorieren, sonst muellen sie den Puffer zu
                return
                
            text = data.decode("utf-8", errors="replace")
            
            self._empfangs_puffer += text

            # Alle vollstaendigen Zeilen verarbeiten
            while "\n" in self._empfangs_puffer:
                zeile, self._empfangs_puffer = self._empfangs_puffer.split(
                    "\n", 1
                )
                zeile = zeile.strip()
                if zeile:
                    self.nachricht.emit(zeile)
        except Exception as e:
            print(f"Fehler im BLE Handler: {e}")

    async def sende_an_hub(self, text):
        """Sendet eine Textnachricht an den Hub (fuer zukuenftige Nutzung)."""
        if self._client and self._client.is_connected:
            try:
                await self._client.write_gatt_char(
                    NUS_RX_UUID, text.encode("utf-8")
                )
            except Exception as e:
                print(f"Fehler im BLE Handler: {e}")
                self.fehler.emit(f"Senden fehlgeschlagen: {e}")
