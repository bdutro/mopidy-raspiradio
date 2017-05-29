from threading import Thread, Event

class StopUpdateException(Exception):
    pass

class AbstractTimerThread(Thread):
    def __init__(self, stop_event, interval, function, *args, **kwargs):
        Thread.__init__(self)
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.stop_event = stop_event
    def run(self):
        return NotImplemented

class Timer(object):
    def __init__(self, thread_type, interval, function, *args, **kwargs):
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.stop_event = Event()
        self.thread = None
        self.thread_type = thread_type

    def start(self):
        self.stop_event.clear()
        self.thread = self.thread_type(self.stop_event, self.interval, self.function, *self.args, **self.kwargs)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join()

    def is_running(self):
        return self.thread.is_alive()

class UpdateInterval(Timer):
    class UpdateThread(AbstractTimerThread):
        def __init__(self, stop_event, interval, function, *args, **kwargs):
            AbstractTimerThread.__init__(self, stop_event, interval, function, *args, **kwargs)

        def run(self):
            while not self.stop_event.wait(self.interval):
                try:
                    self.function(*self.args, **self.kwargs)
                except StopUpdateException:
                    break

    def __init__(self, interval, function, *args, **kwargs):
        Timer.__init__(self, self.UpdateThread, interval, function, *args, **kwargs)

class Timeout(Timer):
    class TimeoutThread(AbstractTimerThread):
        def __init__(self, stop_event, interval, function, *args, **kwargs):
            AbstractTimerThread.__init__(self, stop_event, interval, function, *args, **kwargs)

        def run(self):
            self.stop_event.wait(self.interval)
            self.function(*self.args, **self.kwargs)

    def __init__(self, interval, function, *args, **kwargs):
        Timer.__init__(self, self.TimeoutThread, interval, function, *args, **kwargs)

