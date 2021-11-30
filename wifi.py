import board
import busio
from digitalio import DigitalInOut
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_sdcard
import storage
import time
import os

debug = False

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
sd_cs = DigitalInOut(board.SD_CS)
_sdcard = None
try:
    _sdcard = adafruit_sdcard.SDCard(spi, sd_cs)
    vfs = storage.VfsFat(_sdcard)
    storage.mount(vfs, "/sd")
except OSError as error:
    print("No SD card found:", error)


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32 SPI webclient test")

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_URL = "http://api.coindesk.com/v1/bpi/currentprice/USD.json"


# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

requests.set_socket(socket, esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])

for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap["ssid"], "utf-8"), ap["rssi"]))

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))


def wget(url, filename, *, chunk_size=12000):
    """Download a url and save to filename location, like the command wget.
    :param url: The URL from which to obtain the data.
    :param filename: The name of the file to save the data to.
    :param chunk_size: how much data to read/write at a time.
    """
    print("Fetching stream from", url)

    r = requests.get(url, stream=True)

    if debug:
        print(r.headers)
    content_length = int(r.headers['content-length'])
    remaining = content_length
    print("Saving data to ", filename)
    stamp = time.monotonic()
    file = open(filename, "wb")
    for i in r.iter_content(min(remaining, chunk_size)):  # huge chunks!
        remaining -= len(i)
        file.write(i)
        if debug:
            print("Read %d bytes, %d remaining" % (content_length-remaining, remaining))
        else:
            print(".", end='')
        if not remaining:
            break
    file.close()

    r.close()
    stamp = time.monotonic() - stamp
    print("Created file of %d bytes in %0.1f seconds" % (os.stat(filename)[6], stamp))
    if not content_length == os.stat(filename)[6]:
        raise RuntimeError