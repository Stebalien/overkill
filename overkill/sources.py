##
#    This file is part of Overkill.
#
#    Overkill is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Overkill is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Overkill.  If not, see <http://www.gnu.org/licenses/>.
##

from threading import Thread, Event
from .base import Runnable, Publisher
import select, os
import fcntl
import time
import pyinotify
from . import manager

__all__=("Source", "ThreadedSource", "get_timersource", "get_fdsource", "get_fwsource")

class Source(Runnable, Publisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stop(self, *args, **kwargs):
        for subscription in tuple(self.subscribers.keys()):
            self.push_unsubscribe(subscription)
        return super().stop(*args, **kwargs)

    def subscribe(self, *args, **kwargs):
        self.start()
        super().subscribe(*args, **kwargs)

    def unsubscribe(self, *args, **kwargs):
        super().unsubscribe(*args, **kwargs)
        # Don't need to lock because stop will lock and check
        # running again.
        def later():
            if not self.subscribers and self.running:
                self.stop()
        manager.queue(later)

class InterruptableWaiter:
    def __init__(self):
        self._interrupt_read_fd, self._interrupt_write_fd = os.pipe()
        self._is_set = False

    def interrupt(self):
        if self._is_set:
            return
        self._is_set = True # Prevent repeats (Yay GIL...)
        os.write(self._interrupt_write_fd, bytes(1))


    def select(self, files):
        w, _, _ = select.select(list(files) + [self._interrupt_read_fd], [], [])
        try:
            w.remove(self._interrupt_read_fd)
            os.read(self._interrupt_read_fd, 1)
            self._is_set = False
        except ValueError:
            pass
        return w

class ThreadedSource(Source, Thread):
    def __init__(self):
        super().__init__()

    def start(self):
        if Source.start(self):
            Thread.start(self)
            return True
        return False

    def run(self):
        raise NotImplementedError()

    def stop(self):
        ret = super().stop()
        self.join()
        return ret

class FDManagerSource(ThreadedSource):
    def __init__(self):
        self.__fd_map = {}
        self._waiter = InterruptableWaiter()
        super().__init__()

    def is_publishing(self, subscription):
        return hasattr(subscription, "fileno")

    def run(self):
        while self.running:
            for f in self._waiter.select(self.subscribers.keys()):
                if not f.peek():
                    # EOF
                    self.push_unsubscribe(f)
                    continue
                try:
                    while b'\n' in f.peek():
                        line = f.readline()

                        if not isinstance(line, str):
                            line = line.decode('utf-8')

                        self.push_updates({f: line.rstrip('\n')})
                except:
                    self.push_unsubscribe(f)
        self.running = False

    def on_stop(self):
        self._interrupt()

    def on_subscribe(self, subscriber, subscription):
        flags = fcntl.fcntl(subscription.fileno(), fcntl.F_GETFD)
        fcntl.fcntl(subscription.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self._interrupt()

    def _interrupt(self):
        self._waiter.interrupt()

class FWManagerSource(Source, pyinotify.ProcessEvent):
    def __init__(self):
        super().__init__()
        self.watches = {}
        self.watches_reverse = {}
        self.wm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(self.wm, self)

    def on_start(self):
        self.notifier.start()

    def on_stop(self):
        self.notifier.stop()

    def is_publishing(self, subscription):
        sub = dict(subscription)
        try:
            return sub['path'][0].startswith('/') \
                    and isinstance(sub['mask'], int)
        except:
            return False

    def on_subscribe(self, subscriber, subscription):
        wdd = self.wm.add_watch(**dict(subscription))
        for wd in wdd.values():
            self.watches[wd] = (subscriber, subscription)
        self.watches_reverse[(subscriber, subscription)] = wdd

    def on_unsubscribe(self, subscriber, subscription):
        wdd = self.watches_reverse.pop((subscriber, subscription))
        for wd in wdd.values():
            del self.watches[wd]
            self.wm.del_watch(wd)

    def process_default(self, event):
        try:
            subscriber, subscription = self.watches[event.wd]
            subscriber.handle_updates({subscription: event}, self)
        except:
            pass

class ScheduleEntry:
    def __init__(self, subscriber, early, late):
        self.subscriber = subscriber
        self.early = early
        self.late = late
        self.last = 0

    def __hash__(self):
        return hash((self.subscriber, self.early, self.late))

class TimerSource(ThreadedSource):

    def __init__(self):
        self._interrupt_event = Event()
        self._queue = set()
        super().__init__()

    def run(self):
        while self.running:
            max_delay = None
            ctime = time.time()
            updates = {}
            ctime = time.time()
            for sched in self._queue:
                if (ctime - sched.last) > sched.early:
                    sched.last = ctime
                    updates[(sched.early, sched.late)] = ctime

                    new_max_delay = ctime + sched.late
                    if max_delay is None or new_max_delay < max_delay:
                        max_delay = new_max_delay
            if updates:
                self.push_updates(updates)

            if self._interrupt_event.wait(max_delay and int(max_delay - time.time())):
                # Reenter the queue if something is added
                # I don't care about the actual status
                self._interrupt_event.clear()

    def on_stop(self):
        self._interrupt_event.set()

    def on_subscribe(self, subscriber, subscription):
        self._queue.add(ScheduleEntry(subscriber, *subscription))
        self._interrupt_event.set()

    def on_unsubscribe(self, subscriber, subscription):
        self._queue.remove(ScheduleEntry(subscriber, *subscription))

    def is_publishing(self, subscription):
        try:
            return isinstance(subscription[0], int) and isinstance(subscription[1], int)
        except:
            return False

timersource = None
def get_timersource():
    global timersource
    if not timersource:
        timersource = TimerSource()
    return timersource

fdsource = None
def get_fdsource():
    global fdsource
    if not fdsource:
        fdsource = FDManagerSource()
    return fdsource

fwsource = None
def get_fwsource():
    global fwsource
    if not fwsource:
        fwsource = FWManagerSource()
    return fwsource
