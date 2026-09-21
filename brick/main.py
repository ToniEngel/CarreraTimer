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
ENTPRELLZEIT_MS = 2000    # 2s Sperre nach Ampelstart und zwischen den Runden

# Waehlbare Rundenzahlen (rechter Knopf iteriert durch)
RUNDEN_OPTIONEN = [10, 20, 30, 40, 50]

# Tonausgabe waehrend des Rennens wurde in die Web-App ausgelagert,
# um die Messschleife nicht durch blockierende Beeps zu verlangsamen.


# ---------------------------------------------------------------------------
# Ampel-Hilfsfunktionen
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rundenauswahl-Anzeige (linke Spalte, vor dem Rennen)
# ---------------------------------------------------------------------------

def zeige_rundenauswahl(index):
    """Visualisiert die gewaehlte Rundenzahl in der linken Spalte (Spalte 0).
    index = 0..4 → 1..5 Pixel leuchten von oben nach unten."""
    hub.display.off()
    anzahl_pixel = index + 1  # 1 bis 5
    for zeile in range(5):
        if zeile < anzahl_pixel:
            hub.display.pixel(zeile, 0, 100)
        else:
            hub.display.pixel(zeile, 0, 0)


# ---------------------------------------------------------------------------
# Runden-Fortschrittsanzeige (waehrend des Rennens)
# ---------------------------------------------------------------------------

def zeige_rundenfortschritt(rest_spur1, rest_spur2):
    """Zeigt den Rundenfortschritt beider Spuren auf der 5x5 Matrix.

    Layout:
      Spalte 0: Zehner Spur 1 (je voller 10er ein Pixel, von oben)
      Spalte 1: Einer Spur 1  (je 2er-Schritt ein Pixel; ungerade = 50%)
      Spalte 2: leer (Trenner)
      Spalte 3: Zehner Spur 2
      Spalte 4: Einer Spur 2

    rest = verbleibende Runden (max_runden - gefahrene_runden)
    Zehner = rest // 10  → Pixel 0..(Zehner-1) voll hell
    Einer  = rest % 10   → Pixel 0..(Einer//2 - 1) voll hell
              falls Einer ungerade: naechstes Pixel halb hell (50%)
    """
    hub.display.off()

    for spur_idx, rest in enumerate([rest_spur1, rest_spur2]):
        # Spalten: Spur 1 → 0,1  |  Spur 2 → 3,4
        spalte_zehner = 0 if spur_idx == 0 else 3
        spalte_einer  = 1 if spur_idx == 0 else 4

        zehner = rest // 10
        einer  = rest % 10

        # Zehner-Block (Spalte_zehner): eine Zeile pro voller 10
        for zeile in range(5):
            if zeile < zehner:
                hub.display.pixel(zeile, spalte_zehner, 100)

        # Einer-Block (Spalte_einer): Zweierschritte
        volle_pixel = einer // 2
        halb_pixel  = einer % 2  # 1 wenn ungerade, 0 wenn gerade

        for zeile in range(5):
            if zeile < volle_pixel:
                hub.display.pixel(zeile, spalte_einer, 100)
            elif zeile == volle_pixel and halb_pixel:
                hub.display.pixel(zeile, spalte_einer, 50)


# ---------------------------------------------------------------------------
# Ampelsequenz
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rennen
# ---------------------------------------------------------------------------

def rennen(max_runden):
    """Fuehrt ein komplettes Rennen durch.

    Args:
        max_runden: Anzahl der zu fahrenden Runden.
    """
    timer = StopWatch()
    start_zeit = timer.time()

    # Zustand pro Spur
    runden       = [0, 0]          # Gezaelte Runden [Spur1, Spur2]
    letzte_erk   = [start_zeit, start_zeit]  # 2s Sperre ab Ampelstart (ignoriert erste Ueberfahrt)
    runden_start = [start_zeit, start_zeit]  # Startzeit = Ampel gruen
    fertig       = [False, False]  # Ob die Spur alle Runden beendet hat
    gesamt_zeit  = [0, 0]          # Gesamtzeit bei Finish

    sensoren = [sensor_spur1, sensor_spur2]

    # Initial-Anzeige: volle Runden fuer beide Spuren
    zeige_rundenfortschritt(max_runden, max_runden)

    while not (fertig[0] or fertig[1]):
        jetzt = timer.time()

        for spur in range(2):
            if fertig[spur]:
                continue

            # Entprellzeit pruefen
            if jetzt - letzte_erk[spur] < ENTPRELLZEIT_MS:
                continue

            if sensor_erkennt_auto(sensoren[spur]):
                letzte_erk[spur] = jetzt

                # Erkennung: Runde abgeschlossen
                runden[spur] += 1
                rundenzeit = jetzt - runden_start[spur]
                runden_start[spur] = jetzt

                spur_nr = spur + 1  # 1-basiert fuer Protokoll
                print("LAP:" + str(spur_nr) + ":" + str(runden[spur]) + ":" + str(rundenzeit))

                # Rundenfortschritt auf Matrix aktualisieren
                rest1 = max_runden - runden[0]
                rest2 = max_runden - runden[1]
                zeige_rundenfortschritt(
                    max(rest1, 0),
                    max(rest2, 0)
                )

                # Letzte Runde?
                if runden[spur] >= max_runden:
                    fertig[spur] = True
                    gesamt_zeit[spur] = jetzt
                    print("FINISH:" + str(spur_nr) + ":" + str(jetzt))

        # Kein wait() – so schnell wie moeglich pollen

    # Sieger bestimmen (wer zuerst fertig ist)
    if fertig[0]:
        sieger = 1
    else:
        sieger = 2

    print("WINNER:" + str(sieger))

    # Sieger-Tusch
    spiele_tusch()

    # Status-LED in Siegerfarbe
    sieger_farbe = Color.RED if sieger == 1 else Color.BLUE
    hub.light.on(sieger_farbe)

    # Siegernummer auf Display anzeigen
    hub.display.off()
    wait(300)
    hub.display.char(str(sieger))
    wait(5000)


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main():
    """Hauptprogramm – Rundenwahl per rechtem Knopf, Start per linkem Knopf."""
    hub.display.off()
    hub.light.on(Color.GREEN)
    print("READY")

    # --- Rundenwahl-Index (Default: 0 → 10 Runden) ---
    runden_idx = 0
    zeige_rundenauswahl(runden_idx)

    # Entprellung fuer rechten Knopf
    rechts_letzte = 0
    RECHTS_ENTPRELL = 300  # ms

    wahl_timer = StopWatch()

    while True:
        # ---- Rechter Knopf: Rundenzahl weiterschalten ----
        jetzt = wahl_timer.time()
        if Button.RIGHT in hub.buttons.pressed():
            if jetzt - rechts_letzte > RECHTS_ENTPRELL:
                rechts_letzte = jetzt
                runden_idx = (runden_idx + 1) % len(RUNDEN_OPTIONEN)
                zeige_rundenauswahl(runden_idx)
            wait(20)
            continue

        # ---- Linker Knopf: Rennen starten ----
        if Button.LEFT not in hub.buttons.pressed():
            wait(30)
            continue

        # Taste losgelassen abwarten
        while Button.LEFT in hub.buttons.pressed():
            wait(10)

        wait(200)  # kurze Pause vor Ampel

        max_runden = RUNDEN_OPTIONEN[runden_idx]
        hub.light.on(Color.RED)

        # Rundenzahl an App melden
        print("RUNDEN:" + str(max_runden))

        # Ampelsequenz – wiederholen bei Fruehstart
        sauberer_start = False
        while not sauberer_start:
            sauberer_start = ampelsequenz()
            if not sauberer_start:
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
        rennen(max_runden)

        # Zurueck zum Startbildschirm
        hub.light.on(Color.GREEN)
        ampel_aus()
        print("READY")

        # Rundenwahl-Anzeige wieder einblenden
        runden_idx = 0
        wahl_timer = StopWatch()
        rechts_letzte = 0
        zeige_rundenauswahl(runden_idx)


if __name__ == "__main__":
    main()
