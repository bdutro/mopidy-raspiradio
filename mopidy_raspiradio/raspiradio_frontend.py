import pykka
import re
from threading import Timer, Thread, Event

from mopidy import core
from gui import Gui

class UpdateThread(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        if self.is_running:
            self._timer.cancel()
            self.is_running = False

class RaspiradioFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(RaspiradioFrontend, self).__init__()
        self.core = core
        self.gui = Gui(config['raspiradio'])
        self.update_thread = UpdateThread(1.0/config['raspiradio']['refresh_rate'], self.playback_position_update)
        self.cur_pos = 0

    def start_position_update(self):
        self.update_thread.start()

    def stop_position_update(self):
        self.update_thread.stop()

    def playback_position_update(self):
        progress = self.core.playback.get_time_position()
        new_pos = progress/1000
        if new_pos != cur_pos:
            cur_pos = new_pos
            self.set_progress(progress)

    def track_playback_started(self, tl_track):
        self.stop_position_update()
        track = tl_track.track
        self.gui.set_artist(', '.join(a.name for a in track.artists))
        self.gui.set_album(track.album.name)
        self.gui.set_title(track.name)
        self.gui.set_track(track.track_no)
        self.gui.set_track_length(track.length)
        self.cur_pos = 0
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
