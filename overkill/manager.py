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

from threading import Event, Lock
import sys

manager = None

class Manager:
    def add_source(self, source):
        self.aggregator.add_source(source)

    def add_sink(self, sink):
        self.__sinks.add(sink)

    def __init__(self):
        self.__sinks = set()
        self.__aggregator = None
        self.__int = Event()
        self.__lock = Lock()
        self.__queue = []

    @property
    def aggregator(self):
        if self.__aggregator is None:
            from overkill.processors import Aggregator
            self.__aggregator = Aggregator()
        return self.__aggregator

    def queued(self, fn):
        def do(*args, **kwargs):
            self.queue(fn, args, kwargs)
        return do
    
    def queue(self, fn, args, kwargs):
        with self.__lock:
            self.__queue.append((fn, args, kwargs))
            self.__int.set()

    def run(self):
        try:
            for sink in self.__sinks:
                sink.start()
            while self.__int.wait():
                with self.__lock:
                    self.__int.clear()
                    if not self.__queue:
                        continue
                    waiting = self.__queue
                    self.__queue = []
                for fn, args, kwargs in waiting:
                    try:
                        fn(*args, **kwargs)
                    except:
                        import traceback
                        traceback.print_exc()
        except SystemExit:
            pass
        except BaseException:
            import traceback
            traceback.print_exc()
        finally:
            for sink in self.__sinks:
                try:
                    sink.stop()
                except BaseException as e:
                    print(e)

sys.modules[__name__] = Manager()
