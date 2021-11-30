from widget_manager import Widget, WidgetManager, MED_FONT
import wifi
from secrets import secrets
import displayio
import board
import json
import adafruit_requests as requests
from adafruit_button import Button


DATA_SOURCE = 'http://api.openweathermap.org/data/2.5/weather?id='+secrets['city_id']
DATA_SOURCE += '&appid='+secrets['openweather_token']
DATA_LOCATION = []

class ButtonWidget(Widget):
    def __init__(self, height=40, width=140, 
            style=Button.ROUNDRECT, 
            fill_color=0x000000, 
            outline_color=0xEEEEEE, 
            label="Button", 
            label_font=MED_FONT,
            label_color=0xFFFFFF, 
            **kwargs):
        super().__init__(width=width, height=height, bg=None, **kwargs)
        self.button = Button(
            x=0, 
            y=0, 
            width=width, 
            height=height,
            style=style,
            fill_color=fill_color,
            outline_color=outline_color,
            label=label,
            label_font=label_font,
            label_color=label_color,
        )

    def on_touch(self, touch):
        """Override this method to do an action when touched"""
        pass

    def on_release(self):
        pass


class WeatherWidget(Widget):

    def __init__(self, width=120, height=50, **kwargs):
        super().__init__(width=width, height=height, bg=None, **kwargs)
        self.weather_icon = displayio.Group()
        self.weather_icon.x = 0
        self.weather_icon.y = 0
        self.temp_label = self.add_text(font=MED_FONT, text="XXX F", x=50, y=25)
        self.icon_file = None
        # every 20 minutes check the weather:
        self.add_action(1200, self.get_weather)
        self.append(self.weather_icon)
        self.get_weather()

    def get_weather(self):
        print("Fetching weather...")
        try:
            value = requests.get(DATA_SOURCE).text
            weather = json.loads(value)
            weather_icon_name = weather['weather'][0]['icon']
            try:
                self.weather_icon.pop()
            except IndexError:
                pass
            filename = "/icons/"+weather_icon_name+".bmp"
            if filename:
                if self.icon_file:
                    self.icon_file.close()
                self.icon_file = open(filename, "rb")
                icon = displayio.OnDiskBitmap(self.icon_file)
                try:
                    icon_sprite = displayio.TileGrid(icon,
                                                     pixel_shader=displayio.ColorConverter(),
                                                     x=0, y=0)
                except TypeError:
                    icon_sprite = displayio.TileGrid(icon,
                                                     pixel_shader=displayio.ColorConverter(),
                                                     position=(0, 0))

                self.weather_icon.append(icon_sprite)
            # self.append(self.weather_icon)
            temperature = weather['main']['temp'] - 273.15 # its...in kelvin
            temperature_text = '%3d F' % round(((temperature * 9 / 5) + 32))
            self.temp_label.text = temperature_text
            # board.DISPLAY.refresh_soon()

        except RuntimeError as e:
            print("Error: {}".format(e))


class ImageWidget(Widget):

    converter_service = "https://io.adafruit.com/api/v2/%s/integrations/image-formatter?x-aio-key=%s&width=%d&height=%d&output=BMP%d&url=%s"

    def __init__(self, image_url=None, update_time=3600, bg=None, **kwargs):
        super().__init__(bg=bg, **kwargs)
        self.image_url = image_url
        self.color_depth = 16
        self.add_action(update_time, self.get_image)
        self.get_image()

    """Download an image.
       :param resize (width, height) tuple to resize """
    def get_image(self):
        print("getting image: ", self.image_url)
        if not self.image_url:
            return
        aio_username = secrets['aio_username']
        aio_key = secrets['aio_key']
        fetch_url = self.converter_service % (aio_username, aio_key,
                                              self.width, self.height,
                                              self.color_depth, self.image_url)

        filename="/sd/cache.bmp"
        wifi.wget(fetch_url, filename)
        self.set_background(filename)
