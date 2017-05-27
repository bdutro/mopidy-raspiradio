from luma.core import cmdline, error
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1322, ssd1325, ssd1331, sh1106
from PIL import ImageFont

class Gui(object):
    def __init__(self, args, font_args):
        self.lcd = None
        self.canvas = None
        self.track_info = {}
        
        self.fonts = {}

        for field, font_info in font_args.iteritems():
            self.fonts[field] = ImageFont.truetype(font=font_info['file'], size=font_info['size'])

        parser = cmdline.create_parser('')
        device_args = parser.parse_args(args)

        try:
            self.lcd = cmdline.create_device(device_args)
        except error.Error as e:
            parser.error(e)
        
    def do_draw(self):
        with canvas(self.lcd) as draw:
            y_pos = 0
            for field in ['artist', 'title', 'album']:
                width, height = self.fonts[field].getsize(self.track_info[field])
                draw.text((0, y_pos), self.track_info[field], font=self.fonts[field])
                y_pos += height

    def set_artist(self, artist):
        self.track_info['artist'] = artist

    def set_album(self, album):
        self.track_info['album'] = album

    def set_title(self, title):
        self.track_info['title'] = title

    def set_track(self, track):
        self.track_info['track'] = track

