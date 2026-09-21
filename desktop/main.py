"""
Carrera Timer – Desktop-Anwendung (Einstiegspunkt)

Startet die Qt/QML-Oberflaeche und den BLE-Receiver
fuer die Verbindung mit dem Pybricks Spike Prime Hub.

Nutzung:
    python main.py [--hub-name NAME]
"""

import sys
import os
import signal
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

from ble_receiver import BLEReceiver
from race_controller import RaceController


def main():
    # Ctrl+C soll die App sauber beenden
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Hub-Name aus Kommandozeile oder Default
    hub_name = "Pybricks Hub"
    if "--hub-name" in sys.argv:
        idx = sys.argv.index("--hub-name")
        if idx + 1 < len(sys.argv):
            hub_name = sys.argv[idx + 1]

    # Qt Application
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Carrera Timer")
    app.setOrganizationName("CarreraTimer")

    # Datenmodell
    controller = RaceController()

    # BLE-Receiver
    ble = BLEReceiver(hub_name=hub_name)
    ble.nachricht.connect(controller.verarbeiteNachricht)
    ble.verbunden.connect(controller.setHubVerbunden)
    ble.hubNameGeaendert.connect(controller.setHubName)
    ble.fehler.connect(controller.setBleFehler)
    ble.debugNachricht.connect(controller.setLetzteAktivitaet)

    # QML Engine
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("raceController", controller)

    # QML-Datei laden
    qml_datei = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_datei)))

    if not engine.rootObjects():
        print("Fehler: QML konnte nicht geladen werden!", file=sys.stderr)
        sys.exit(1)

    # BLE starten
    ble.start()

    # App ausfuehren
    exit_code = app.exec()

    # Aufräumen
    ble.stop()
    ble.wait(3000)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
