import pykka
import re
from threading import Timer, Thread, Event

from mopidy import core
from gui import Gui

class UpdateInterval(object):
    class UpdateThread(Thread):
        def __init__(self, stop_event, interval, function, *args, **kwargs):
            Thread.__init__(self)
            self._timer     = None
            self.interval   = interval
            self.function   = function
            self.args       = args
            self.kwargs     = kwargs
            self.is_running = False
            self.stop_event = stop_event

        def run(self):
            self.is_running = True
            while not self.stop_event.wait(self.interval):
                self.function(*self.args, **self.kwargs)

    def __init__(self, interval, function, *args, **kwargs):
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.stop_event = Event()
        self._thread = None

    def start(self):
        self.stop_event.clear()
        self._thread = self.UpdateThread(self.stop_event, self.interval, self.function, *self.args, **self.kwargs)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self.stop_event.set()
        if self._thread is not None:
            self._thread.join()

class RaspiradioFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(RaspiradioFrontend, self).__init__()
        self.core = core
        self.gui = Gui(config['raspiradio'])
        self.update_thread = UpdateInterval(1.0/config['raspiradio']['refresh_rate'], self.playback_position_update)
        self.cur_pos = 0

    def start_position_update(self):
        self.update_thread.start()

    def stop_position_update(self):
        self.update_thread.stop()

    def playback_position_update(self):
        progress = self.core.playback.get_time_position().get()
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
