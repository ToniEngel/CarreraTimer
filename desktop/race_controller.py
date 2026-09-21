"""
Rennlogik und QML-Datenmodell fuer den Carrera-Timer.

Empfaengt Nachrichten vom BLE-Receiver, verwaltet den Rennzustand
und stellt alle Daten als QML-Properties bereit.
"""

from PySide6.QtCore import QObject, Signal, Slot, Property


def format_zeit(ms):
    """Formatiert Millisekunden als mm:ss.xxx String."""
    if ms <= 0:
        return "--:--.---"
    minuten = ms // 60000
    rest = ms % 60000
    sekunden = rest // 1000
    millis = rest % 1000
    return f"{minuten:02d}:{sekunden:02d}.{millis:03d}"


class SpurDaten:
    """Hilfsobjekt fuer die Daten einer einzelnen Spur."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.runde = 0
        self.letzte_zeit_ms = 0
        self.beste_zeit_ms = 0
        self.gesamt_ms = 0
        self.fertig = False
        self.alle_zeiten = []


class RaceController(QObject):
    """QML-Datenmodell fuer das Rennen.

    Wird als Context-Property in QML registriert und stellt
    alle Renn-Daten als Properties und Signale bereit.
    """

    # Signale fuer Property-Aenderungen
    maxRundenChanged = Signal()
    spur1RundeChanged = Signal()
    spur2RundeChanged = Signal()
    spur1LetzteZeitChanged = Signal()
    spur2LetzteZeitChanged = Signal()
    spur1BesteZeitChanged = Signal()
    spur2BesteZeitChanged = Signal()
    spur1FertigChanged = Signal()
    spur2FertigChanged = Signal()
    siegerSpurChanged = Signal()
    fruehstartSpurChanged = Signal()
    ampelStatusChanged = Signal()
    rennLaeuftChanged = Signal()
    hubVerbundenChanged = Signal()
    bleFehlerChanged = Signal()
    hubNameChanged = Signal()
    letzteAktivitaetChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_runden = 10
        self._spur = [SpurDaten(), SpurDaten()]
        self._sieger_spur = 0
        self._fruehstart_spur = 0
        self._ampel_status = 0
        self._renn_laeuft = False
        self._hub_verbunden = False
        self._hub_name = ""
        self._ble_fehler = ""
        self._letzte_aktivitaet = ""

    # --- Properties ---

    @Property(int, notify=maxRundenChanged)
    def maxRunden(self):
        return self._max_runden

    @maxRunden.setter
    def maxRunden(self, wert):
        if self._max_runden != wert and wert > 0:
            self._max_runden = wert
            self.maxRundenChanged.emit()

    @Property(int, notify=spur1RundeChanged)
    def spur1Runde(self):
        return self._spur[0].runde

    @Property(int, notify=spur2RundeChanged)
    def spur2Runde(self):
        return self._spur[1].runde

    @Property(str, notify=spur1LetzteZeitChanged)
    def spur1LetzteZeit(self):
        return format_zeit(self._spur[0].letzte_zeit_ms)

    @Property(str, notify=spur2LetzteZeitChanged)
    def spur2LetzteZeit(self):
        return format_zeit(self._spur[1].letzte_zeit_ms)

    @Property(str, notify=spur1BesteZeitChanged)
    def spur1BesteZeit(self):
        return format_zeit(self._spur[0].beste_zeit_ms)

    @Property(str, notify=spur2BesteZeitChanged)
    def spur2BesteZeit(self):
        return format_zeit(self._spur[1].beste_zeit_ms)

    @Property(bool, notify=spur1FertigChanged)
    def spur1Fertig(self):
        return self._spur[0].fertig

    @Property(bool, notify=spur2FertigChanged)
    def spur2Fertig(self):
        return self._spur[1].fertig

    @Property(int, notify=siegerSpurChanged)
    def siegerSpur(self):
        return self._sieger_spur

    @Property(int, notify=fruehstartSpurChanged)
    def fruehstartSpur(self):
        return self._fruehstart_spur

    @Property(int, notify=ampelStatusChanged)
    def ampelStatus(self):
        return self._ampel_status

    @Property(bool, notify=rennLaeuftChanged)
    def rennLaeuft(self):
        return self._renn_laeuft

    @Property(bool, notify=hubVerbundenChanged)
    def hubVerbunden(self):
        return self._hub_verbunden

    @Property(str, notify=hubNameChanged)
    def hubName(self):
        return self._hub_name

    @Property(str, notify=letzteAktivitaetChanged)
    def letzteAktivitaet(self):
        return self._letzte_aktivitaet

    @Property(str, notify=bleFehlerChanged)
    def bleFehler(self):
        return self._ble_fehler

    # --- Slots (von QML oder BLE aufgerufen) ---

    @Slot(int)
    def setMaxRunden(self, wert):
        """Setzt die maximale Rundenanzahl."""
        self.maxRunden = wert

    @Slot()
    def resetFruehstart(self):
        """Setzt die Fruehstart-Anzeige zurueck."""
        if self._fruehstart_spur != 0:
            self._fruehstart_spur = 0
            self.fruehstartSpurChanged.emit()

    # --- Nachrichtenverarbeitung ---

    @Slot(str)
    def verarbeiteNachricht(self, nachricht):
        """Verarbeitet eine Protokoll-Nachricht vom Hub."""
        print(f"[BLE EMPFANG] {nachricht}")
        teile = nachricht.split(":")

        if not teile:
            return

        befehl = teile[0]

        if befehl == "READY":
            self._reset_rennen()

        elif befehl == "AMPEL" and len(teile) >= 2:
            try:
                stufe = int(teile[1])
                self._ampel_status = stufe
                self.ampelStatusChanged.emit()
            except ValueError:
                pass

        elif befehl == "GO":
            self._ampel_status = 0
            self.ampelStatusChanged.emit()
            self._renn_laeuft = True
            self.rennLaeuftChanged.emit()
            # Fruehstart zuruecksetzen
            self._fruehstart_spur = 0
            self.fruehstartSpurChanged.emit()

        elif befehl == "FALSE_START" and len(teile) >= 2:
            try:
                spur = int(teile[1])
                self._fruehstart_spur = spur
                self.fruehstartSpurChanged.emit()
                # Ampel zuruecksetzen
                self._ampel_status = 0
                self.ampelStatusChanged.emit()
                self._renn_laeuft = False
                self.rennLaeuftChanged.emit()
            except ValueError:
                pass

        elif befehl == "LAP" and len(teile) >= 4:
            try:
                spur = int(teile[1]) - 1  # 0-basiert
                runde = int(teile[2])
                zeit_ms = int(teile[3])

                if 0 <= spur <= 1:
                    self._spur[spur].runde = runde
                    self._spur[spur].letzte_zeit_ms = zeit_ms
                    self._spur[spur].alle_zeiten.append(zeit_ms)

                    # Beste Zeit aktualisieren
                    if (
                        self._spur[spur].beste_zeit_ms == 0
                        or zeit_ms < self._spur[spur].beste_zeit_ms
                    ):
                        self._spur[spur].beste_zeit_ms = zeit_ms

                    # Signale senden
                    if spur == 0:
                        self.spur1RundeChanged.emit()
                        self.spur1LetzteZeitChanged.emit()
                        self.spur1BesteZeitChanged.emit()
                    else:
                        self.spur2RundeChanged.emit()
                        self.spur2LetzteZeitChanged.emit()
                        self.spur2BesteZeitChanged.emit()
            except ValueError:
                pass

        elif befehl == "FINISH" and len(teile) >= 3:
            try:
                spur = int(teile[1]) - 1  # 0-basiert
                gesamt_ms = int(teile[2])

                if 0 <= spur <= 1:
                    self._spur[spur].fertig = True
                    self._spur[spur].gesamt_ms = gesamt_ms

                    if spur == 0:
                        self.spur1FertigChanged.emit()
                    else:
                        self.spur2FertigChanged.emit()
            except ValueError:
                pass

        elif befehl == "WINNER" and len(teile) >= 2:
            try:
                sieger = int(teile[1])
                self._sieger_spur = sieger
                self.siegerSpurChanged.emit()
                self._renn_laeuft = False
                self.rennLaeuftChanged.emit()
            except ValueError:
                pass

    @Slot(bool)
    def setHubVerbunden(self, status):
        """Aktualisiert den Hub-Verbindungsstatus."""
        if self._hub_verbunden != status:
            self._hub_verbunden = status
            self.hubVerbundenChanged.emit()

    @Slot(str)
    def setHubName(self, name):
        """Setzt den Namen des aktuell verbundenen Hubs."""
        if self._hub_name != name:
            self._hub_name = name
            self.hubNameChanged.emit()

    @Slot(str)
    def setLetzteAktivitaet(self, text):
        """Aktualisiert die letzte Aktivitaet."""
        if self._letzte_aktivitaet != text:
            self._letzte_aktivitaet = text
            self.letzteAktivitaetChanged.emit()

    @Slot(str)
    def setBleFehler(self, text):
        """Aktualisiert die BLE-Fehlermeldung."""
        if self._ble_fehler != text:
            self._ble_fehler = text
            self.bleFehlerChanged.emit()

    def _reset_rennen(self):
        """Setzt alle Renndaten zurueck fuer ein neues Rennen."""
        for spur in self._spur:
            spur.reset()

        self._sieger_spur = 0
        self._fruehstart_spur = 0
        self._ampel_status = 0
        self._renn_laeuft = False

        self.spur1RundeChanged.emit()
        self.spur2RundeChanged.emit()
        self.spur1LetzteZeitChanged.emit()
        self.spur2LetzteZeitChanged.emit()
        self.spur1BesteZeitChanged.emit()
        self.spur2BesteZeitChanged.emit()
        self.spur1FertigChanged.emit()
        self.spur2FertigChanged.emit()
        self.siegerSpurChanged.emit()
        self.fruehstartSpurChanged.emit()
        self.ampelStatusChanged.emit()
        self.rennLaeuftChanged.emit()
