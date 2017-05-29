import time
from luma.core import cmdline, error
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1322, ssd1325, ssd1331, sh1106
from PIL import ImageFont
import timers

class ProgressBar(object):
    __progress_padding = 2
    __progress_height = 10
    __progress_width = 5
    __progress_line_width = 2
    __progress_x_offset = __progress_width/2
    __progress_y_offset = __progress_height/2
    __time_format = '%M:%S'

    def __init__(self, y_pos, lcd_width, font):
        self.font = font
        y_pos += self.__progress_padding
        progress_line_y_pos = y_pos + self.__progress_y_offset
        self.progress_line_extents = [(self.__progress_x_offset, progress_line_y_pos), (lcd_width - self.__progress_x_offset, progress_line_y_pos)]
        self.progress_marker_y_extents = (y_pos, y_pos + self.__progress_height)
        self.progress = 0
        self.track_length = None
        self.scale_factor = None
        self.time_str = '- / -'

    def draw(self, canvas):
        if self.track_length is None:
            progress_pos = 0
            final_time_str = '- / -'
        else:
            progress_pos = int(round(self.progress * self.scale_factor))
            final_time_str = self.time_str.format(self.format_time(self.progress))

        canvas.line([(progress_pos, self.progress_marker_y_extents[0]), (progress_pos, self.progress_marker_y_extents[1])], width=self.__progress_width)
        canvas.line(self.progress_line_extents, width=self.__progress_line_width)
        canvas.text((self.__progress_x_offset, self.progress_marker_y_extents[1]), final_time_str, font=self.font)

    def set_progress(self, progress):
        self.progress = progress

    def format_time(self, t):
        return time.strftime(self.__time_format, time.gmtime(t))

    def set_track_length(self, track_length):
        self.track_length = track_length
        self.scale_factor = float(self.progress_line_extents[1][0]) / self.track_length
        self.time_str = '{} / ' + self.format_time(track_length)

def find_center(total_width, object_width):
    return int(round(float(total_width - object_width) / 2))

class UI(object):
    def __init__(self, lcd, device_args, config):
        pass
    def on_switch_to(self):
        pass
    def on_switch_from(self):
        pass

class Clock(UI):
    __clock_str = '%I:%M %p'

    def __init__(self, lcd, device_args, config):
        UI.__init__(self, lcd, device_args, config)
        self.lcd = lcd
        self.font = ImageFont.truetype(font=config['clock_font_file'], size=config['clock_font_size'])
        self.update_thread = timers.UpdateInterval(1.0/config['refresh_rate'], self.tick)
        self.cur_time = time.time()
        _, height = self.font.getsize(self.format_time())
        self.y_pos = find_center(device_args.height, height)
        self.lcd_width = device_args.width

    def format_time(self):
        return time.strftime(self.__clock_str, time.localtime(self.cur_time))

    def tick(self, force_redraw=False):
        new_time = time.time()
        if new_time != self.cur_time:
            self.cur_time = new_time
            self.draw()

    def start(self):
        self.update_thread.start()

    def stop(self):
        self.update_thread.stop()

    def draw(self):
        with canvas(self.lcd) as cvs:
            time_str = self.format_time()
            width, _ = self.font.getsize(time_str)
            x_pos = find_center(self.lcd_width, width)
            cvs.text((x_pos, self.y_pos), time_str, font=self.font)

    def on_switch_to(self):
        self.tick(force_redraw=True)
        self.start()

    def on_switch_from(self):
        self.stop()

class PlaybackDisplay(UI):
    __fields = ['title', 'artist', 'album']
    def __init__(self, lcd, device_args, config):
        UI.__init__(self, lcd, device_args, config)
        self.lcd = lcd
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

        self.progress_bar = ProgressBar(y_pos,
                                        device_args.width,
                                        ImageFont.truetype(font=config['progress_bar_font_file'],
                                                           size=config['progress_bar_font_size']))

    def draw_trackinfo(self, draw):
        for field in self.__fields:
            draw.text((0, self.fonts_y_pos[field]), self.track_info[field], font=self.fonts[field])
    
    def draw(self):
        with canvas(self.lcd) as cvs:
            self.draw_trackinfo(cvs)
            self.progress_bar.draw(cvs)

    def set_artist(self, artist):
        self.track_info['artist'] = artist

    def set_album(self, album):
        self.track_info['album'] = album

    def set_title(self, title):
        self.track_info['title'] = title

    def set_track(self, track):
        self.track_info['track'] = track

    def set_track_length(self, length):
        self.progress_bar.set_track_length(length)

    def set_progress(self, progress):
        self.progress_bar.set_progress(progress)

class GuiModes:
    CLOCK = 0
    PLAYBACK = 1

class Gui(object):
    __ui_types = { GuiModes.CLOCK: Clock,
                   GuiModes.PLAYBACK: PlaybackDisplay
                 }
    def __init__(self, config):
        self.mode = None
        self.uis = {}
        self.cur_ui = None

        parser = cmdline.create_parser('')
        device_args = parser.parse_args(config['lcd_config'].split(' '))

        try:
            lcd = cmdline.create_device(device_args)
        except error.Error as e:
            parser.error(e)

        for ui_type, ui_cls in self.__ui_types.iteritems():
            self.uis[ui_type] = ui_cls(lcd, device_args, config)

    def get_mode(self):
        return self.mode

    def set_mode(self, mode):
        self.mode = mode
        if self.cur_ui is not None:
            self.cur_ui.on_switch_from()
        self.cur_ui = self.uis[self.mode]
        self.cur_ui.on_switch_to()

    def get_ui(self):
        return self.cur_ui
