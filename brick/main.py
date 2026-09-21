"""
Carrera-Renntimer – Pybricks Brick-Programm
Fuer LEGO Spike Prime Hub mit Pybricks v4.0+

Zwei Farbsensoren (Port A und B) messen Rundenzeiten
auf einer Carrera-Rennbahn. Daten werden per print()
ueber BLE UART an die Desktop-App gesendet.

Protokoll:
    READY               - Hub bereit
    AMPEL:n             - Ampel-Stufe n (1-5)
    GO                  - Start!
    FALSE_START:spur    - Fruehstart auf Spur 1 oder 2
    LAP:spur:runde:ms   - Rundenzeit
    FINISH:spur:ms      - Alle Runden beendet
    WINNER:spur         - Sieger
"""

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import ColorSensor
from pybricks.parameters import Port, Button, Color
from pybricks.tools import wait, StopWatch
from urandom import randint

# --- Hardware ---
hub = PrimeHub()
sensor_spur1 = ColorSensor(Port.A)
sensor_spur2 = ColorSensor(Port.B)

# --- Konfiguration ---
SCHWELLWERT = 30          # reflection() > SCHWELLWERT → Auto erkannt
ENTPRELLZEIT_MS = 500     # Mindestzeit zwischen zwei Erkennungen pro Spur
MAX_RUNDEN = 10           # Wird spaeter ggf. per BLE vom Laptop ueberschrieben

# --- Ampel-Muster (5 Zeilen, je 5 LEDs) ---
def ampel_zeile_an(zeile):
    """Schaltet eine Zeile (0-4) der 5x5 Matrix auf volle Helligkeit."""
    for spalte in range(5):
        hub.display.pixel(zeile, spalte, 100)


def ampel_aus():
    """Schaltet die gesamte LED-Matrix aus."""
    hub.display.off()


def blinke_warnung(anzahl=5):
    """Laesst die Matrix als Warnung blinken (Fruehstart)."""
    for _ in range(anzahl):
        hub.display.char('X')
        wait(200)
        hub.display.off()
        wait(200)


def spiele_tusch():
    """Spielt eine Sieger-Fanfare (C-Dur Arpeggio aufwaerts)."""
    hub.speaker.beep(523, 120)   # C5
    wait(30)
    hub.speaker.beep(659, 120)   # E5
    wait(30)
    hub.speaker.beep(784, 120)   # G5
    wait(30)
    hub.speaker.beep(1046, 400)  # C6
    wait(100)
    hub.speaker.beep(1046, 400)  # C6 nochmal
    wait(50)
    hub.speaker.beep(1318, 600)  # E6 lang


def sensor_erkennt_auto(sensor):
    """Prueft ob ein Sensor gerade ein Auto erkennt."""
    return sensor.reflection() > SCHWELLWERT


def pruefe_fruehstart():
    """Prueft waehrend der Ampelphase ob ein Auto zu frueh startet.
    Gibt die Spur-Nummer zurueck (1 oder 2) oder 0 wenn kein Fruehstart."""
    if sensor_erkennt_auto(sensor_spur1):
        return 1
    if sensor_erkennt_auto(sensor_spur2):
        return 2
    return 0


def ampelsequenz():
    """Fuehrt die F1-Ampelsequenz durch.

    Returns:
        True wenn sauberer Start, False wenn Fruehstart erkannt.
    """
    ampel_aus()
    wait(500)

    # 5 Reihen nacheinander einschalten (ca. 1 Sekunde pro Reihe)
    for zeile in range(5):
        ampel_zeile_an(zeile)
        hub.speaker.beep(800, 80)
        print("AMPEL:" + str(zeile + 1))

        # Waehrend der Wartezeit: Fruehstart pruefen
        timer = StopWatch()
        while timer.time() < 1000:
            frueh = pruefe_fruehstart()
            if frueh > 0:
                print("FALSE_START:" + str(frueh))
                blinke_warnung()
                return False
            wait(5)

    # Alle 5 Lichter an – zufaellige Pause (wie echter F1-Start)
    # Zwischen 0.2 und 3.0 Sekunden
    zufalls_pause = 200 + randint(0, 2800)
    timer = StopWatch()
    while timer.time() < zufalls_pause:
        frueh = pruefe_fruehstart()
        if frueh > 0:
            print("FALSE_START:" + str(frueh))
            blinke_warnung()
            return False
        wait(5)

    # LIGHTS OUT – GO!
    ampel_aus()
    hub.speaker.beep(1200, 150)
    print("GO")
    return True


def rennen(max_runden):
    """Fuehrt ein komplettes Rennen durch.

    Args:
        max_runden: Anzahl der zu fahrenden Runden.
    """
    timer = StopWatch()

    # Zustand pro Spur
    runden = [0, 0]                # Aktuelle Runde [Spur1, Spur2]
    letzte_erkennung = [0, 0]      # Zeitstempel letzte Erkennung
    runden_start = [0, 0]          # Zeitstempel Rundenstart
    gestartet = [False, False]     # Ob die Spur die Startlinie ueberfahren hat
    fertig = [False, False]        # Ob die Spur alle Runden beendet hat
    gesamt_zeit = [0, 0]           # Gesamtzeit bei Finish

    sensoren = [sensor_spur1, sensor_spur2]

    while not (fertig[0] or fertig[1]):
        jetzt = timer.time()

        for spur in range(2):
            if fertig[spur]:
                continue

            # Entprellzeit pruefen
            if jetzt - letzte_erkennung[spur] < ENTPRELLZEIT_MS:
                continue

            # Wir nehmen den aktuellen Wert
            if sensor_erkennt_auto(sensoren[spur]):
                letzte_erkennung[spur] = jetzt

                if not gestartet[spur]:
                    # Erste Erkennung: Auto ueberquert Startlinie
                    gestartet[spur] = True
                    runden_start[spur] = jetzt
                else:
                    # Weitere Erkennung: Runde abgeschlossen
                    runden[spur] += 1
                    rundenzeit = jetzt - runden_start[spur]
                    runden_start[spur] = jetzt

                    spur_nr = spur + 1  # 1-basiert fuer Protokoll
                    print("LAP:" + str(spur_nr) + ":" + str(runden[spur]) + ":" + str(rundenzeit))

                    # Aktuelle Runde auf Display anzeigen
                    # (Zeigt die Rundennummer der fuehrenden Spur)
                    max_runde = max(runden[0], runden[1])
                    if max_runde <= 99:
                        hub.display.number(max_runde)

                    # Letzte Runde?
                    if runden[spur] >= max_runden:
                        fertig[spur] = True
                        gesamt_zeit[spur] = jetzt
                        print("FINISH:" + str(spur_nr) + ":" + str(jetzt))

        # Kein wait() – so schnell wie moeglich pollen

    # Sieger bestimmen (wer zuerst fertig ist)
    if fertig[0] and not fertig[1]:
        sieger = 1
    elif fertig[1] and not fertig[0]:
        sieger = 2
    else:
        # Falls wirklich beide exakt gleichzeitig (unwahrscheinlich)
        if gesamt_zeit[0] <= gesamt_zeit[1]:
            sieger = 1
        else:
            sieger = 2

    print("WINNER:" + str(sieger))

    # Sieger-Tusch
    spiele_tusch()

    # Sieger auf Display anzeigen
    hub.display.off()
    wait(300)
    hub.display.char(str(sieger))
    wait(3000)


# --- Hauptprogramm ---
def main():
    """Hauptprogramm – wartet auf Tastendruck und startet Rennen."""
    hub.display.off()
    hub.light.on(Color.GREEN)

    print("READY")

    while True:
        # Warte auf linke Taste
        while Button.LEFT not in hub.buttons.pressed():
            wait(50)

        # Taste losgelassen abwarten
        while Button.LEFT in hub.buttons.pressed():
            wait(10)

        wait(200)  # Kurze Pause

        hub.light.on(Color.RED)

        # Ampelsequenz – wiederholen bei Fruehstart
        sauberer_start = False
        while not sauberer_start:
            sauberer_start = ampelsequenz()
            if not sauberer_start:
                # Bei Fruehstart: warte auf erneuten Tastendruck
                hub.light.on(Color.ORANGE)
                print("READY")
                while Button.LEFT not in hub.buttons.pressed():
                    wait(50)
                while Button.LEFT in hub.buttons.pressed():
                    wait(10)
                wait(200)
                hub.light.on(Color.RED)

        # Rennen starten
        hub.light.on(Color.GREEN)
        rennen(MAX_RUNDEN)

        # Zurueck zum Startbildschirm
        hub.light.on(Color.GREEN)
        ampel_aus()
        print("READY")


if __name__ == "__main__":
    main()
