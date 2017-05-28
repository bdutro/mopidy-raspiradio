import pykka
import re
from threading import Timer, Thread, Event

from mopidy import core
from gui import Gui

class UpdateThread(Thread):
    def __init__(self, event, interval, callback):
        super(Thread, self).__init__()
        self.stopped = event
        self.interval = interval
        self.callback = callback

    def run(self):
        while not self.stopped.wait(self.interval):
            self.callback()

class RaspiradioFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(RaspiradioFrontend, self).__init__()
        self.core = core
        self.gui = Gui(config['raspiradio'])
        self.stop_update_flag = Event()
        self.update_thread = UpdateThread(self.stop_update_flag, 1, self.playback_position_update)
    
    def start_position_update(self):
        self.update_thread.start()

    def stop_position_update(self):
        self.stop_update_flag.set()

    def playback_position_update(self):
        self.set_progress(self.core.get_time_position())

    def track_playback_started(self, tl_track):
        self.stop_position_update()
        track = tl_track.track
        self.gui.set_artist(', '.join(a.name for a in track.artists))
        self.gui.set_album(track.album.name)
        self.gui.set_title(track.name)
        self.gui.set_track(track.track_no)
        self.gui.set_track_length(track.length)
        self.set_progress(0)
        self.start_position_update()

    def track_playback_ended(self, tl_track, time_position):
        self.stop_position_update()
        self.set_progress(time_position)

    def track_playback_paused(self, tl_track, time_position):
        self.stop_position_update()
        self.set_progress(time_position)

    def track_playback_resumed(self, tl_track, time_position):
        self.set_progress(time_position)
        self.start_position_update()

    def seeked(self, time_position):
        self.stop_position_update()
        self.set_progress(time_position)
        self.start_position_update()

    def set_progress(self, progress):
        self.gui.set_progress(progress)
        self.gui.do_draw()
