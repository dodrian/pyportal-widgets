import displayio
import board
import time
from adafruit_display_text.label import Label
import adafruit_touchscreen
import gc
from adafruit_bitmap_font import bitmap_font


LARGE_FONT = bitmap_font.load_font('/fonts/PTSans-Regular-50px.bdf')
LARGE_FONT.load_glyphs(b'0123456789:X')

MED_FONT = bitmap_font.load_font('/fonts/PTSans-Regular-24px.bdf')
MED_FONT.load_glyphs(b'0123456789CF:X')


touchscreen = adafruit_touchscreen.Touchscreen(board.TOUCH_XL, board.TOUCH_XR,
                                               board.TOUCH_YD, board.TOUCH_YU,
                                               calibration=((5200, 59000),
                                                            (5800, 57000)),
                                               size=(320, 240))

gc.collect()


class Widget(displayio.Group):

    def __init__(self, x=0, y=0, width=320, height=240, bg=0x0, **kwargs):
        super().__init__(x=x, y=y, **kwargs)
        self.touched = False
        self._bg_group = displayio.Group()
        self.actions = []
        self.width = width
        self.height = height
        super().append(self._bg_group)
        self.set_background(bg)
        # board.DISPLAY.refresh_soon()
    
    def contains(self, point):
        return (self.x <= point[0] <= self.x + self.width) and (
            self.y <= point[1] <= self.y + self.height
        )

    def add_text(self, font, text, x=0, y=0):
        label = Label(font, text=text)
        label.x = x
        label.y = y
        self.append(label)
        return label

    """Add a function callback to be done every interval seconds"""
    def add_action(self, interval, action):
        self.actions.append({'last_action': 0,
                             'interval':    interval,
                             'action':      action})

    """Handles actions, or can be overridden for a continously updating widget"""
    def tick(self):
        seconds = time.monotonic()
        for act in self.actions:
            if seconds > act['last_action'] + act['interval']:
                act['last_action'] = seconds
                act['action']()

    def touch(self, touch):
        if self.touched == False:
            self.on_touch(touch)
            self.touched = True
        pass

    def on_touch(self, touch):
        """Override this method to do an action when touched"""
        pass

    def on_release(self):
        pass

    def set_background(self, bg):
        while self._bg_group:
            self._bg_group.pop()
        if bg is None:
            return  # nothing to do
        if isinstance(bg, str):  # set to image
            self._bg_file = open(bg, "rb")
            self._bg_bitmap = displayio.OnDiskBitmap(self._bg_file)
            self.background = displayio.TileGrid(self._bg_bitmap,
                                        pixel_shader=displayio.ColorConverter(),
                                        x=0, y=0)
        elif isinstance(bg, int):
            bgpalette = displayio.Palette(1)
            bgpalette[0] = bg
            self.background = displayio.TileGrid(
                bitmap=displayio.Bitmap(self.width, self.height, 1),
                pixel_shader=bgpalette,
                x=0, y=0,
            )
        else:
            raise RuntimeError("Unknown type of background")
        self._bg_group.append(self.background)
        # board.DISPLAY.refresh_soon()


class WidgetManager(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widgets = []

    def append(self, widget):
        self.widgets.append(widget)
        super().append(widget)

    def start(self):
        while(True):
            for widget in self.widgets:
                widget.tick()

            #  handle touch
            tp = touchscreen.touch_point
            if tp:
                self.touched = True
                print(tp)
                for widget in self.widgets:
                    if widget.contains(tp):
                        widget.touch(tp)
                    elif widget.touched:
                        widget.touched = False
                        widget.on_release()
            else:
                if self.touched:
                    self.touched=False
                    for widget in self.widgets:
                        if widget.touched:
                            widget.touched = False
                            widget.on_release()
                
