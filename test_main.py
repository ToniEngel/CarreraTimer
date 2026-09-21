from pybricks.hubs import PrimeHub
from pybricks.pupdevices import ColorSensor
from pybricks.parameters import Port, Button, Color, Icon
from pybricks.tools import wait, StopWatch
from urandom import randint

hub = PrimeHub()

def ampel_zeile_an(zeile):
    for spalte in range(5):
        hub.display.pixel(zeile, spalte, 100)

def ampel_aus():
    hub.display.off()

def ampelsequenz():
    ampel_aus()
    wait(500)
    for zeile in range(5):
        ampel_zeile_an(zeile)
        hub.speaker.beep(800, 80)
        print("AMPEL:" + str(zeile + 1))
        wait(1000)

def main():
    print("READY")
    # Simulate button press
    wait(200)
    hub.light.on(Color.RED)
    ampelsequenz()
    print("DONE")

main()
