from luma.core import cmdline, error
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1322, ssd1325, ssd1331, sh1106
from PIL import ImageFont

class Gui(object):
    __fields = ['title', 'artist', 'album']
    __progress_padding = 2
    __progress_height = 10
    __progress_width = 5
    __progress_line_width = 2
    __progress_x_offset = __progress_width/2
    __progress_y_offset = __progress_height/2

    def __init__(self, config):
        self.lcd = None
        self.canvas = None
        self.track_info = {}
        self.progress = 0
        
        self.fonts = {}
        self.fonts_y_pos = {}

        y_pos = 0
        for field in self.__fields:
            font = ImageFont.truetype(font=config[field + '_font_file'], size=config[field + '_font_size'])
            self.fonts[field] = font
            self.fonts_y_pos[field] = y_pos
            _, height = font.getsize('M')
            y_pos += height

        parser = cmdline.create_parser('')
        device_args = parser.parse_args(config['lcd_config'].split(' '))

        try:
            self.lcd = cmdline.create_device(device_args)
        except error.Error as e:
            parser.error(e)

        self.lcd_width = device_args.width
        y_pos += self.__progress_padding
        progress_line_y_pos = y_pos + self.__progress_y_offset
        self.progress_line_extents = [(self.__progress_x_offset, progress_line_y_pos), (self.lcd_width - self.__progress_x_offset, progress_line_y_pos)]
        self.progress_marker_y_extents = (y_pos, y_pos + self.__progress_height)

    def draw_trackinfo(self, draw):
        for field in self.__fields:
            draw.text((0, self.fonts_y_pos[field]), self.track_info[field], font=self.fonts[field])
    
    def draw_progressbar(self, draw):
        progress_pos = int(round(float(self.progress)/self.track_length*self.lcd_width))
        draw.line(self.progress_line_extents, width=self.__progress_line_width)
        draw.line([(progress_pos, self.progress_marker_y_extents[0]), (progress_pos, self.progress_marker_y_extents[1])], width=self.__progress_width)

    def do_draw(self):
        with canvas(self.lcd) as draw:
            self.draw_trackinfo(draw)
            self.draw_progressbar(draw)

    def set_artist(self, artist):
        self.track_info['artist'] = artist

    def set_album(self, album):
        self.track_info['album'] = album

    def set_title(self, title):
        self.track_info['title'] = title

    def set_track(self, track):
        self.track_info['track'] = track

    def set_track_length(self, length):
        self.track_length = length

    def set_progress(self, progress):
        self.progress = progress
