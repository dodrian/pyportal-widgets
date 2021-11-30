import time
import json
from secrets import secrets
import board
from adafruit_pyportal import PyPortal
from adafruit_bitmap_font import bitmap_font
import analogio
import displayio
from adafruit_display_text.label import Label
from widget_manager import Widget, WidgetManager, MED_FONT, LARGE_FONT
from widgets import *
import wifi


# Create the WidgetManager
wm = WidgetManager()

#  Load and position Widgets
weather_window = WeatherWidget(x=0, y=0)
wm.append(weather_window)

# quick widget setup
time_window = Widget(bg=None, x=180, y=0, height=40, width=140)
time_window.time_label = time_window.add_text(font=LARGE_FONT, text="XX:XX", x=2, y=20)

def update_time():  # create time update method
    current_time = time.localtime()
    ttext = '%02d:%02d' % (current_time.tm_hour,current_time.tm_min)
    time_window.time_label.text = ttext
    # board.DISPLAY.refresh_soon()

time_window.add_action(1, update_time) # update time every second
wm.append(time_window)  # add to window manager


#  Utilizing ImageWidget
class KittenWidget(ImageWidget):

    def __init__(self, width=320, height=240, **kwargs):
        image_url = "http://placekitten.com/%s/%s" % (width, height)
        super().__init__(image_url=image_url, width=width, height=height, **kwargs)


kw = KittenWidget(width=180, height=180, x=0, y=60)
wm.append(kw)

my_button = ButtonWidget(x=180, y=40)
wm.append(my_button)

# show the window manager
board.DISPLAY.show(wm)

# Start event loop
wm.start()
