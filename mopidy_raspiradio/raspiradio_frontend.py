import pykka
import re

from mopidy import core
import gui
import timers

class RaspiradioFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(RaspiradioFrontend, self).__init__()
        self.core = core
        self.cur_ui = None
        self.gui = gui.Gui(config['raspiradio'])
        self.set_gui_mode(gui.GuiModes.CLOCK)
        self.update_thread = timers.UpdateInterval(1.0/config['raspiradio']['refresh_rate'], self.playback_position_update)
        self.cur_pos = 0
        self.timeout_thread = timers.Timeout(config['raspiradio']['inactivity_timeout'], self.switch_to_clock)

    def start_position_update(self):
        self.update_thread.start()

    def stop_position_update(self):
        self.update_thread.stop()

    def playback_position_update(self):
        try:
            self.set_progress(self.core.playback.get_time_position().get())
        except pykka.exceptions.ActorDeadError:
            raise timers.StopUpdateException
    
    def switch_to_clock(self):
        self.set_gui_mode(gui.GuiModes.CLOCK)

    def get_gui_mode(self):
        return self.gui.get_mode()

    def set_gui_mode(self, mode):
        self.gui.set_mode(mode)
        self.cur_ui = self.gui.get_ui()

    def start_timeout(self):
        self.timeout_thread.start()

    def cancel_timeout(self):
        self.timeout_thread.stop()
        if self.get_gui_mode() != gui.GuiModes.PLAYBACK:
            self.set_gui_mode(gui.GuiModes.PLAYBACK)

    def track_playback_started(self, tl_track):
        self.cancel_timeout()
        self.stop_position_update()
        track = tl_track.track
        self.cur_ui.set_artist(', '.join(a.name for a in track.artists))
        self.cur_ui.set_album(track.album.name)
        self.cur_ui.set_title(track.name)
        self.cur_ui.set_track(track.track_no)
        self.cur_ui.set_track_length(track.length/1000)
        self.set_progress(0, force_redraw=True)
        self.start_position_update()

    def track_playback_ended(self, tl_track, time_position):
        self.start_timeout()
        self.stop_position_update()
        self.set_progress(time_position, force_redraw=True)

    def track_playback_paused(self, tl_track, time_position):
        self.start_timeout()
        self.stop_position_update()
        self.set_progress(time_position, force_redraw=True)

    def track_playback_resumed(self, tl_track, time_position):
        self.cancel_timeout()
        self.set_progress(time_position, force_redraw=True)
        self.start_position_update()

    def seeked(self, time_position):
        self.stop_position_update()
        self.set_progress(time_position, force_redraw=True)
        self.start_position_update()

    def set_progress(self, progress, force_redraw=False):
        new_pos = progress/1000
        if new_pos != self.cur_pos or force_redraw:
            self.cur_pos = new_pos
            self.cur_ui.set_progress(self.cur_pos)
            self.cur_ui.draw()
