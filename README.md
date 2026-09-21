# Carrera Timer 🏎️

Zeitmesssystem für eine Carrera-Rennbahn mit zwei Spuren, basierend auf
**LEGO Spike Prime** (Pybricks v4.0+) und einer **PySide6/QML**-Oberfläche.

## Features

- **F1-Rennstart** mit 5-stufiger Ampelsequenz auf der 5×5 LED-Matrix
- **Frühstart-Erkennung** – wird auf dem Bildschirm angezeigt
- **Live-Rundenzeiten** für beide Spuren
- **Schnellste Runde** wird hervorgehoben
- **Konfigurierbare Rundenanzahl** über die Desktop-Oberfläche
- **Sieger-Anzeige** mit Tusch auf dem Brick

## Hardware-Setup

| Komponente       | Port |
|-----------------|------|
| Farbsensor Spur 1 | A  |
| Farbsensor Spur 2 | B  |

Die Sensoren werden direkt hinter der Startlinie platziert, so dass die
Rennautos (~1–2 cm darüber) beim Überfahren erkannt werden.

## Installation

### Desktop-App

```bash
cd desktop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Brick-Programm

```bash
# Pybricks-Firmware muss auf dem Spike Prime Hub installiert sein
pybricksdev run ble brick/main.py
```

## Protokoll (BLE UART)

Der Brick sendet Nachrichten per `print()` über BLE:

| Nachricht | Bedeutung |
|---|---|
| `READY` | Hub bereit, wartet auf Start |
| `AMPEL:n` | Ampel-LED n (1–5) an |
| `GO` | Lichter aus, Rennen gestartet |
| `FALSE_START:spur` | Frühstart auf Spur 1 oder 2 |
| `LAP:spur:runde:zeit_ms` | Rundenzeit |
| `FINISH:spur:gesamt_ms` | Spur hat alle Runden beendet |
| `WINNER:spur` | Sieger |
