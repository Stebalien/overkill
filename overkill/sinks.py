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

from .base import Runnable, Subscriber, Subprocess
from .sources import get_fdsource, get_fwsource, get_timersource
import subprocess, pyinotify
import stat, os

class Sink(Runnable, Subscriber):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stop(self, *args, **kwargs):
        for subscription, sources  in self.subscriptions.items():
            for source in sources:
                source.unsubscribe(self, subscription)
        self.subscriptions = {}
        return super().stop(*args, **kwargs)

class SimpleSink(Sink):
    subscription = None

    def start(self):
        if super().start():
            self.subscribe_to(self.subscription)
            return True
        return False

    def handle_updates(self, updates, source):
        self.handle_update(updates[self.subscription])

    def handle_update(self, update):
        raise NotImplementedError()

class ReaderSink(Sink):

    def _start_with_source(self, source):
        self.source_file = source
        self.subscribe_to(source, get_fdsource())

    def handle_unsubscribe(self, subscription, source):
        self.stop()

    def handle_updates(self, updates, source):
        try:
            line = updates[self.source_file]
        except KeyError:
            return
        self.handle_input(line)

    def handle_input(self, line):
        raise NotImplementedError()

class FifoSink(ReaderSink):
    fifo_path = None
    create = False
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__starting = False

    def start(self):
        status = False
        with self._state_lock:
            if self.__starting:
                return False
            else:
                self.__starting = True

        if not self.running:
            if not os.path.exists(self.fifo_path):
                if self.create:
                    os.mkfifo(self.fifo_path)
                else:
                    raise RuntimeError()
            self.fifo_file = open(self.fifo_path)
            self._start_with_source(self.fifo_file)
            status = super().start()
            if not self.running:
                self.stop()
                status = False

        self.__starting = False
        return status
    
    def _can_publish(self):
        return self.create or os.path.exists(self.fifo_path) and stat.S_ISFIFO(os.stat(self.fifo_path).st_mode)

    def stop(self):
        if super().stop():
            try:
                self.fifo_file.close()
            except:
                pass
            return True
        return False

class PipeSink(Subprocess, ReaderSink):
    stdout = subprocess.PIPE

    def handle_unsubscribe(self, subscription, source):
        # Restart on crash
        if not self._maybe_restart():
            super().handle_unsubscribe(subscription, source)
    
    def _start_subprocess(self):
        if super()._start_subprocess():
            self._start_with_source(self.proc.stdout)
            return True
        return False

class InotifySink(Sink):
    watches = []

    def handle_unsubscribe(self, subscription, source):
        self.stop()

    def start(self):
        if super().start():
            for watch in self.watches:
                self.watch(**watch)
            return True
        return False

    def watch(self, **args):
        self.subscribe_to(frozenset(args.items()), get_fwsource())
    
    def handle_updates(self, updates, source):
        for sub, event in updates.items():
            if sub not in self.subscriptions:
                continue
            self.file_changed(event)

    def file_changed(self, path, mask):
        raise NotImplementedError()

class FilecountSink(InotifySink):
        add_events = pyinotify.IN_MOVED_TO | pyinotify.IN_CREATE
        remove_events = pyinotify.IN_MOVED_FROM | pyinotify.IN_DELETE
        watchdirs = []
        _count = None

        def start(self):
            if not self.watches:
                all_events = self.add_events | self.remove_events
                self.watches = [{"path": wdir, "mask": all_events} for wdir in self.watchdirs]
            # Initialize Count
            # Asking for it initializes and sends it
            self.count
            return super().start()

        def matches(self, path):
            return True

        @property
        def count(self):
            if self._count is None:
                self.count = sum(sum(
                    1 for f in os.listdir(mdir)
                    if self.matches(os.path.join(mdir, f))
                ) for mdir in self.watchdirs)
            return self._count

        @count.setter
        def count(self, value):
            if (self._count != value):
                self._count = value
                self.count_changed(self._count)

        def file_changed(self, event):
            if not self.matches(event.pathname):
                return
            if event.mask & self.add_events:
                self.count += 1
            elif event.mask & self.remove_events:
                self.count -= 1
            else:
                return

        def count_changed(self, count):
            raise NotImplementedError()

class TimerSink(Sink):
    MIN_INTERVAL = None
    MAX_INTERVAL = None
    timersource = None

    def handle_unsubscribe(self, subscription, source):
        self.stop()
    
    def start(self):
        if super().start():
            self.timersource = get_timersource()
            self.subscribe_to((self.MIN_INTERVAL, self.MAX_INTERVAL), self.timersource)
            return True
        return False

    def handle_updates(self, updates, source):
        # Always check (allow multiple source classes.
        if source == self.timersource:
            self.tick()

    def tick(self):
        raise NotImplementedError()
