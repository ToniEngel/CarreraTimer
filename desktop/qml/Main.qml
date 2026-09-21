import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: fenster
    visible: true
    width: 1200
    height: 800
    minimumWidth: 900
    minimumHeight: 600
    title: "Carrera Timer"
    color: "#0a0a0f"

    // ── Schriften ──
    // Nutze System-Monospace-Fonts (Menlo auf macOS, Consolas auf Windows)
    readonly property string fontZeit: "Menlo"

    // ── Farben ──
    readonly property color farbeSpur1: "#ff2d2d"
    readonly property color farbeSpur1Glow: "#ff4444"
    readonly property color farbeSpur2: "#2d7fff"
    readonly property color farbeSpur2Glow: "#448aff"
    readonly property color farbeBesteZeit: "#b040ff"
    readonly property color farbeHintergrund: "#0a0a0f"
    readonly property color farbeKarte: "#14141f"
    readonly property color farbeKarteRand: "#252535"
    readonly property color farbeText: "#e8e8f0"
    readonly property color farbeTextGedaempft: "#6e6e8a"
    readonly property color farbeAmpelRot: "#ff1a1a"
    readonly property color farbeAmpelAus: "#1a1a25"
    readonly property color farbeFruehstart: "#ff6600"
    readonly property color farbeGewinner: "#ffd700"

    // ── Hintergrund mit Carbon-Muster ──
    Canvas {
        anchors.fill: parent
        z: -1
        onPaint: {
            var ctx = getContext("2d")
            ctx.fillStyle = farbeHintergrund
            ctx.fillRect(0, 0, width, height)

            // Subtiles Raster-Muster
            ctx.strokeStyle = "#12121a"
            ctx.lineWidth = 0.5
            var schritt = 20
            for (var x = 0; x < width; x += schritt) {
                ctx.beginPath()
                ctx.moveTo(x, 0)
                ctx.lineTo(x, height)
                ctx.stroke()
            }
            for (var y = 0; y < height; y += schritt) {
                ctx.beginPath()
                ctx.moveTo(0, y)
                ctx.lineTo(width, y)
                ctx.stroke()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

        // ═══════════════════════════════════════════
        // HEADER
        // ═══════════════════════════════════════════
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            // Titel
            Text {
                text: "🏎️ CARRERA TIMER"
                color: farbeText
                font.pixelSize: 28
                font.bold: true
                font.letterSpacing: 3
            }

            Item { Layout.fillWidth: true }

            // Rundenanzahl-Anzeige (wird vom Hub gesetzt)
            RowLayout {
                spacing: 8

                Text {
                    text: "RUNDEN:"
                    color: farbeTextGedaempft
                    font.pixelSize: 14
                    font.bold: true
                    font.letterSpacing: 1
                }

                Text {
                    text: raceController.maxRunden
                    color: farbeText
                    font.pixelSize: 18
                    font.bold: true
                }
            }

            // Verbindungsstatus
            Rectangle {
                width: statusZeile.width + 20
                height: 32
                radius: 16
                color: raceController.hubVerbunden ? "#0d2f0d" : "#2f0d0d"
                border.color: raceController.hubVerbunden ? "#1a5c1a" : "#5c1a1a"
                border.width: 1

                RowLayout {
                    id: statusZeile
                    anchors.centerIn: parent
                    spacing: 6

                    Rectangle {
                        width: 8; height: 8; radius: 4
                        color: raceController.hubVerbunden ? "#44ff44" : "#ff4444"

                        SequentialAnimation on opacity {
                            running: !raceController.hubVerbunden
                            loops: Animation.Infinite
                            NumberAnimation { to: 0.3; duration: 600 }
                            NumberAnimation { to: 1.0; duration: 600 }
                        }
                    }

                    Text {
                        text: raceController.hubVerbunden ? (raceController.hubName !== "" ? raceController.hubName.toUpperCase() : "VERBUNDEN") : "GETRENNT"
                        color: raceController.hubVerbunden ? "#44ff44" : "#ff8888"
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 1
                    }
                }
            }
        }

        // ═══════════════════════════════════════════
        // F1 AMPEL
        // ═══════════════════════════════════════════
        Rectangle {
            id: ampelBox
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            radius: 12
            color: farbeKarte
            border.color: farbeKarteRand
            border.width: 1
            visible: raceController.ampelStatus > 0 || ampelAusAnimation.running

            RowLayout {
                anchors.centerIn: parent
                spacing: 24

                Repeater {
                    model: 5

                    Rectangle {
                        required property int index
                        width: 50; height: 50; radius: 25
                        color: (index < raceController.ampelStatus) ? farbeAmpelRot : farbeAmpelAus
                        border.color: (index < raceController.ampelStatus) ? "#ff3333" : "#2a2a35"
                        border.width: 2

                        // Glüh-Effekt
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width + 16; height: parent.height + 16
                            radius: width / 2
                            color: "transparent"
                            border.color: farbeAmpelRot
                            border.width: 2
                            opacity: (index < raceController.ampelStatus) ? 0.3 : 0
                            Behavior on opacity { NumberAnimation { duration: 200 } }
                        }

                        Behavior on color { ColorAnimation { duration: 150 } }

                        // Puls-Animation beim Einschalten
                        SequentialAnimation on scale {
                            id: pulsAnim
                            NumberAnimation { to: 1.15; duration: 100; easing.type: Easing.OutQuad }
                            NumberAnimation { to: 1.0; duration: 200; easing.type: Easing.InOutQuad }
                        }

                        // Trigger wenn dieses Licht gerade angeschaltet wird
                        Connections {
                            target: raceController
                            function onAmpelStatusChanged() {
                                if (index < raceController.ampelStatus) {
                                    pulsAnim.restart()
                                }
                            }
                        }
                    }
                }
            }

            // "Lights out"-Animation
            NumberAnimation on opacity {
                id: ampelAusAnimation
                running: false
                from: 1; to: 0; duration: 500
            }

            Connections {
                target: raceController
                function onRennLaeuftChanged() {
                    if (raceController.rennLaeuft) {
                        ampelAusAnimation.restart()
                    }
                }
                function onAmpelStatusChanged() {
                    // Beim ersten Aufleuchten der Ampel opacity zuruecksetzen,
                    // damit sie nach einem vorherigen Rennen wieder sichtbar ist
                    if (raceController.ampelStatus === 1) {
                        ampelAusAnimation.stop()
                        ampelBox.opacity = 1
                    }
                }
            }
        }

        // ═══════════════════════════════════════════
        // ZWEI SPUR-PANELS
        // ═══════════════════════════════════════════
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20

            // --- SPUR 1 ---
            SpurPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spurNummer: 1
                spurName: "SPUR 1"
                spurFarbe: farbeSpur1
                spurGlow: farbeSpur1Glow
                runde: raceController.spur1Runde
                maxRunden: raceController.maxRunden
                letzteZeit: raceController.spur1LetzteZeit
                besteZeit: raceController.spur1BesteZeit
                istFertig: raceController.spur1Fertig
                istSieger: raceController.siegerSpur === 1
            }

            // Trennlinie
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 2
                color: farbeKarteRand
                opacity: 0.5
            }

            // --- SPUR 2 ---
            SpurPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spurNummer: 2
                spurName: "SPUR 2"
                spurFarbe: farbeSpur2
                spurGlow: farbeSpur2Glow
                runde: raceController.spur2Runde
                maxRunden: raceController.maxRunden
                letzteZeit: raceController.spur2LetzteZeit
                besteZeit: raceController.spur2BesteZeit
                istFertig: raceController.spur2Fertig
                istSieger: raceController.siegerSpur === 2
            }
        }

        // ═══════════════════════════════════════════
        // STATUS-LEISTE
        // ═══════════════════════════════════════════
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            radius: 6
            color: "#0c0c14"
            border.color: farbeKarteRand
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: {
                    if (raceController.bleFehler !== "")
                        return raceController.bleFehler
                    if (raceController.rennLaeuft)
                        return "🏁 Rennen läuft..."
                    if (raceController.siegerSpur > 0)
                        return "🏆 Rennen beendet"
                    return "Drücke die linke Taste am Hub zum Starten"
                }
                color: farbeTextGedaempft
                font.pixelSize: 12
                font.letterSpacing: 0.5
            }
        }

        // ═══════════════════════════════════════════
        // DEBUG-LEISTE
        // ═══════════════════════════════════════════
        Text {
            Layout.fillWidth: true
            text: "Letzte BLE Aktivität: " + raceController.letzteAktivitaet
            color: "#666688"
            font.pixelSize: 10
            horizontalAlignment: Text.AlignRight
        }
    }

    // ═══════════════════════════════════════════
    // FRÜHSTART-OVERLAY
    // ═══════════════════════════════════════════
    Rectangle {
        id: fruehstartOverlay
        anchors.fill: parent
        color: "#cc000000"
        visible: raceController.fruehstartSpur > 0
        z: 100

        MouseArea {
            anchors.fill: parent
            onClicked: raceController.resetFruehstart()
        }

        Column {
            anchors.centerIn: parent
            spacing: 20

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "⚠️"
                font.pixelSize: 80

                SequentialAnimation on scale {
                    running: fruehstartOverlay.visible
                    loops: Animation.Infinite
                    NumberAnimation { to: 1.2; duration: 300 }
                    NumberAnimation { to: 1.0; duration: 300 }
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "FRÜHSTART!"
                color: farbeFruehstart
                font.pixelSize: 64
                font.bold: true
                font.letterSpacing: 5

                SequentialAnimation on opacity {
                    running: fruehstartOverlay.visible
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.4; duration: 400 }
                    NumberAnimation { to: 1.0; duration: 400 }
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Spur " + raceController.fruehstartSpur
                color: raceController.fruehstartSpur === 1 ? farbeSpur1 : farbeSpur2
                font.pixelSize: 36
                font.bold: true
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Klicken um fortzufahren"
                color: farbeTextGedaempft
                font.pixelSize: 16
            }
        }
    }

    // ═══════════════════════════════════════════
    // SIEGER-OVERLAY
    // ═══════════════════════════════════════════
    Rectangle {
        id: siegerOverlay
        anchors.fill: parent
        color: "#dd000000"
        visible: raceController.siegerSpur > 0
        z: 90

        // Konfetti-Partikel
        Repeater {
            model: 40

            Rectangle {
                required property int index
                property real startX: Math.random() * fenster.width
                property real startDelay: Math.random() * 2000
                property color konfettiColor: {
                    var farben = ["#ff2d2d", "#2d7fff", "#ffd700", "#44ff44", "#ff44ff", "#44ffff"]
                    return farben[index % farben.length]
                }

                x: startX + Math.sin(fallAnim.value * 3 + index) * 30
                y: -20
                width: 6 + Math.random() * 6
                height: width * (1 + Math.random())
                radius: Math.random() > 0.5 ? width / 2 : 0
                color: konfettiColor
                rotation: fallAnim.value * (200 + index * 10)
                opacity: siegerOverlay.visible ? 0.8 : 0
                visible: siegerOverlay.visible

                NumberAnimation on y {
                    id: fallAnim
                    property real value: 0
                    running: siegerOverlay.visible
                    from: -20 - startDelay * 0.3
                    to: fenster.height + 50
                    duration: 3000 + Math.random() * 2000
                    loops: Animation.Infinite

                    onRunningChanged: {
                        if (running) value = 0
                    }
                }

                NumberAnimation on rotation {
                    running: siegerOverlay.visible
                    from: 0; to: 360
                    duration: 2000 + Math.random() * 2000
                    loops: Animation.Infinite
                }
            }
        }

        Column {
            anchors.centerIn: parent
            spacing: 24
            z: 10

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "🏆"
                font.pixelSize: 100

                SequentialAnimation on scale {
                    running: siegerOverlay.visible
                    loops: Animation.Infinite
                    NumberAnimation { to: 1.15; duration: 800; easing.type: Easing.InOutQuad }
                    NumberAnimation { to: 1.0; duration: 800; easing.type: Easing.InOutQuad }
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "SIEGER"
                color: farbeGewinner
                font.pixelSize: 56
                font.bold: true
                font.letterSpacing: 8

                SequentialAnimation on opacity {
                    running: siegerOverlay.visible
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.7; duration: 1000 }
                    NumberAnimation { to: 1.0; duration: 1000 }
                }
            }

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: siegerSpurText.width + 60
                height: 70
                radius: 16
                color: raceController.siegerSpur === 1 ? farbeSpur1 : farbeSpur2
                border.color: farbeGewinner
                border.width: 2

                Text {
                    id: siegerSpurText
                    anchors.centerIn: parent
                    text: "SPUR " + raceController.siegerSpur
                    color: "white"
                    font.pixelSize: 36
                    font.bold: true
                    font.letterSpacing: 4
                }
            }
        }
    }

    // ═══════════════════════════════════════════
    // SPUR-PANEL KOMPONENTE
    // ═══════════════════════════════════════════
    component SpurPanel: Rectangle {
        id: panel

        property int spurNummer: 1
        property string spurName: "SPUR"
        property color spurFarbe: "#ff0000"
        property color spurGlow: "#ff4444"
        property int runde: 0
        property int maxRunden: 10
        property string letzteZeit: "--:--.---"
        property string besteZeit: "--:--.---"
        property bool istFertig: false
        property bool istSieger: false

        radius: 16
        color: farbeKarte
        border.color: istSieger ? farbeGewinner : farbeKarteRand
        border.width: istSieger ? 2 : 1

        // Oberer Farbstreifen
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 4
            radius: 2
            color: panel.spurFarbe

            // Glow-Effekt
            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                color: panel.spurGlow
                opacity: 0.5
                layer.enabled: true
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            anchors.topMargin: 28
            spacing: 16

            // Spur-Name
            Text {
                text: panel.spurName
                color: panel.spurFarbe
                font.pixelSize: 20
                font.bold: true
                font.letterSpacing: 3
            }

            // Runden-Anzeige
            RowLayout {
                spacing: 8

                Text {
                    text: "RUNDE"
                    color: farbeTextGedaempft
                    font.pixelSize: 13
                    font.letterSpacing: 1
                }

                Text {
                    text: panel.runde + " / " + panel.maxRunden
                    color: farbeText
                    font.pixelSize: 22
                    font.bold: true
                }
            }

            // Fortschrittsbalken
            Rectangle {
                Layout.fillWidth: true
                height: 8
                radius: 4
                color: "#1a1a28"

                Rectangle {
                    width: panel.maxRunden > 0
                           ? parent.width * Math.min(panel.runde / panel.maxRunden, 1.0)
                           : 0
                    height: parent.height
                    radius: parent.radius
                    color: panel.spurFarbe
                    opacity: 0.8

                    Behavior on width {
                        NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                    }
                }
            }

            Item { Layout.fillHeight: true; Layout.preferredHeight: 8 }

            // ── LETZTE RUNDENZEIT ──
            Text {
                text: "LETZTE RUNDE"
                color: farbeTextGedaempft
                font.pixelSize: 11
                font.letterSpacing: 1.5
                font.bold: true
            }

            Text {
                id: letzteZeitText
                text: panel.letzteZeit
                color: farbeText
                font.pixelSize: 48
                font.bold: true
                font.family: fenster.fontZeit
                font.letterSpacing: 2

                // Aufleuchten bei neuer Zeit
                SequentialAnimation on color {
                    id: zeitFlash
                    ColorAnimation { to: panel.spurGlow; duration: 100 }
                    ColorAnimation { to: farbeText; duration: 500 }
                }

                Connections {
                    target: raceController
                    function onSpur1LetzteZeitChanged() {
                        if (panel.spurNummer === 1) zeitFlash.restart()
                    }
                    function onSpur2LetzteZeitChanged() {
                        if (panel.spurNummer === 2) zeitFlash.restart()
                    }
                }
            }

            Item { Layout.fillHeight: true; Layout.preferredHeight: 4 }

            // ── BESTE RUNDENZEIT ──
            Rectangle {
                Layout.fillWidth: true
                height: besteZeitSpalte.height + 20
                radius: 10
                color: "#18102a"
                border.color: "#2a1a4a"
                border.width: 1
                visible: panel.runde > 0

                ColumnLayout {
                    id: besteZeitSpalte
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.margins: 14
                    spacing: 4

                    RowLayout {
                        spacing: 6
                        Text {
                            text: "⚡"
                            font.pixelSize: 14
                        }
                        Text {
                            text: "BESTE RUNDE"
                            color: farbeBesteZeit
                            font.pixelSize: 11
                            font.letterSpacing: 1.5
                            font.bold: true
                        }
                    }

                    Text {
                        text: panel.besteZeit
                        color: farbeBesteZeit
                        font.pixelSize: 28
                        font.bold: true
                        font.family: fenster.fontZeit
                        font.letterSpacing: 1
                    }
                }
            }

            Item { Layout.fillHeight: true }

            // Finish-Anzeige
            Rectangle {
                Layout.fillWidth: true
                height: 44
                radius: 10
                visible: panel.istFertig
                color: panel.istSieger ? "#2a2400" : "#1a1a28"
                border.color: panel.istSieger ? farbeGewinner : farbeKarteRand
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: panel.istSieger ? "🏆 GEWONNEN!" : "🏁 FERTIG"
                    color: panel.istSieger ? farbeGewinner : farbeText
                    font.pixelSize: 18
                    font.bold: true
                    font.letterSpacing: 2
                }
            }
        }
    }
}
