from threading import Timer, Thread, Event

class StopUpdateException(Exception):
    pass

class UpdateInterval(object):
    class UpdateThread(Thread):
        def __init__(self, stop_event, interval, function, *args, **kwargs):
            Thread.__init__(self)
            self._timer     = None
            self.interval   = interval
            self.function   = function
            self.args       = args
            self.kwargs     = kwargs
            self.stop_event = stop_event

        def run(self):
            while not self.stop_event.wait(self.interval):
                try:
                    self.function(*self.args, **self.kwargs)
                except StopUpdateException:
                    break

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


