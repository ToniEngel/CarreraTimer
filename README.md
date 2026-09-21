# Carrera Timer 🏎️

Ein modernes, webbasiertes Zeitmesssystem für eine Carrera-Rennbahn mit zwei Spuren.
Das System nutzt einen **LEGO Spike Prime Hub** (mit Pybricks v4.0+) als Sensoreinheit und eine **Web-App** (HTML/JS) für die Anzeige, welche direkt via Web Bluetooth mit dem Hub kommuniziert.

## ✨ Features

- **Direkte BLE-Verbindung:** Kein PC oder Proxy nötig! Die Web-App verbindet sich direkt aus dem Browser (z.B. Chrome am Mac oder Bluefy am iPad) mit dem Pybricks Hub.
- **F1-Rennstart & Frühstart-Erkennung:** 5-stufige Ampelsequenz. Bei einem Frühstart blinkt die Ampel rot und die Spur wird angezeigt.
- **Präzises Timing:** Die Rundenzeit startet exakt bei "Grün" (nicht beim ersten Sensor-Überfahren). Eine 2-Sekunden-Sperre nach dem Start verhindert Fehlmessungen.
- **Live-Rundenzeiten & Matrix-Anzeige:** Fortschritt wird direkt auf der 5x5 LED-Matrix des Hubs (Zehner und Einer-Schritte) sowie in der App angezeigt.
- **Rundenauswahl direkt am Hub:** Vor dem Start kann über den rechten Knopf am Hub zwischen 10, 20, 30, 40 oder 50 Runden gewählt werden (Visualisierung am linken Rand der LED-Matrix).
- **Firebase-Leaderboard:** Bestzeiten werden automatisch pro Spur inklusive Datum in einer Firebase-Datenbank gesichert.
- **Akustisches Feedback:** Unterschiedliche kurze Töne pro Spur bei Rundendurchfahrt, sowie Sieger-Fanfare am Ende.

## 📱 Die Web-App (Empfohlen)

Die App kann ohne Installation direkt im Browser aufgerufen werden.

👉 **[Web-App öffnen](https://ToniEngel.github.io/CarreraTimer/)**

- **Mac/PC:** Öffne den Link in Google Chrome oder MS Edge (Web Bluetooth wird in Safari nicht unterstützt).
- **iPad/iOS:** Nutze die App **Bluefy** (oder WebBLE) aus dem App Store, da Apple Web Bluetooth in Standard-Browsern blockiert.

## 🛠 Hardware-Setup

| Komponente       | Port |
|-----------------|------|
| Farbsensor Spur 1 | A  |
| Farbsensor Spur 2 | B  |

Die Sensoren werden direkt hinter der Startlinie platziert, so dass die Rennautos (~1–2 cm darüber) beim Überfahren erkannt werden.

## 💻 Brick-Programm (Installation)

Der Pybricks-Code muss auf dem Spike Prime Hub laufen.

```bash
# Pybricks-Firmware muss auf dem Spike Prime Hub installiert sein
# Dauerhaftes Speichern auf dem Hub (empfohlen): 
# Nutze https://code.pybricks.com, um die brick/main.py auf den Hub zu laden.

# Alternativ lokales Starten:
pybricksdev run ble brick/main.py
```

## 📡 Protokoll (BLE UART)

Der Brick sendet Nachrichten per `print()` über BLE:

| Nachricht | Bedeutung |
|---|---|
| `READY` | Hub bereit, wartet auf Start |
| `RUNDEN:n` | `n` Runden wurden am Hub eingestellt |
| `AMPEL:n` | Ampel-LED n (1–5) an |
| `GO` | Lichter aus, Rennen gestartet (Timer startet!) |
| `FALSE_START:spur` | Frühstart auf Spur 1 oder 2 |
| `LAP:spur:runde:zeit_ms` | Rundenzeit |
| `FINISH:spur:gesamt_ms` | Spur hat alle Runden beendet |
| `WINNER:spur` | Sieger (inkl. Fanfare) |

*(Hinweis: Eine ältere Desktop-Version der App in Python/PySide6 befindet sich noch im Ordner `/desktop`)*
