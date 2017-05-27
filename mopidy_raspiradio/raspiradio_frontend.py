import pykka
import re

from mopidy import core
from gui import Gui

class RaspiradioFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(RaspiradioFrontend, self).__init__()
        self.core = core
        lcd_args = []
        font_args = {}
        font_args_re = re.compile('(.+)_font')

        for opt, val in config.items('lcd'):
            lcd_args.append('--{}'.format(opt))
            lcd_args.append(val)
        for opt, val in config.items('raspiradio'):
            font_match = font_args_re.match(opt)
            if font_match:
                font_vals = val.split(',')
                font_args[font_match.group(1)] = {
                        'file': font_vals[0],
                        'size': font_vals[1]
                }

        self.gui = Gui(lcd_args, font_args)
    def track_playback_started(tl_track):
        track = tl_track.track
        self.gui.set_artist(', '.join(a.name for a in track.artists))
        self.gui.set_album(track.album.name)
        self.gui.set_title(track.name)
        self.gui.set_track(track.track_no)
        self.gui.do_draw()
