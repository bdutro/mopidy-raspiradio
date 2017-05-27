import pykka
import re

from mopidy import core
from gui import Gui

class RaspiradioFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(RaspiradioFrontend, self).__init__()
        self.core = core

        self.gui = Gui(config)

    def track_playback_started(tl_track):
        track = tl_track.track
        self.gui.set_artist(', '.join(a.name for a in track.artists))
        self.gui.set_album(track.album.name)
        self.gui.set_title(track.name)
        self.gui.set_track(track.track_no)
        self.gui.do_draw()
