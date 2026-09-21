import asyncio
from bleak import BleakScanner

PYBRICKS_SERVICE_UUID = "C5F50001-8280-46DA-89F4-6D8051E4AEEF"

async def main():
    print("Suche nach Pybricks Hubs...")
    devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
    found = False
    for addr, (device, adv_data) in devices.items():
        uuids = [u.lower() for u in adv_data.service_uuids]
        if PYBRICKS_SERVICE_UUID.lower() in uuids or (device.name and "Pybricks" in device.name):
            print(f"Gefunden: Name = '{device.name}', Adresse = {device.address}")
            found = True
             
    if not found:
        print("Kein Hub gefunden.")

asyncio.run(main())
