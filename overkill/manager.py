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

# Note: Global imports won't work (because we set the module).

manager = None
class Manager:
    def add_source(self, source):
        self.aggregator.add_source(source)

    def add_sink(self, sink):
        self.__sinks.add(sink)

    def __init__(self):
        import queue
        self.__sinks = set()
        self.__aggregator = None
        self.__queue = queue.Queue()

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
    
    def queue(self, fn, args=None, kwargs=None):
        self.__queue.put((fn, args, kwargs))

    def __flush_queue(self):
        import queue
        while self.__queue:
            try:
                task = self.__queue.get_nowait()
            except queue.Empty:
                return
            self.__handle_task(task)

    def __handle_task(self, task):
        fn, args, kwargs = task
        try:
            fn(*(args or ()), **(kwargs or {}))
        except Exception:
            import traceback
            traceback.print_exc()

    def run(self):
        import signal

        signal.signal(signal.SIGTERM, lambda signal, frame: sys.exit(0))

        try:
            for sink in self.__sinks:
                sink.start()
            while True:
                self.__handle_task(self.__queue.get())
        except SystemExit:
            pass
        except KeyboardInterrupt:
            pass
        except BaseException:
            import traceback
            traceback.print_exc()
        finally:
            # Flush queue
            self.__flush_queue()
            for sink in self.__sinks:
                try:
                    sink.stop()
                    self.__flush_queue()
                except BaseException:
                    import traceback
                    traceback.print_exc()
            if self.__aggregator is not None:
                self.__aggregator.stop()
                self.__flush_queue()

import sys

sys.modules[__name__] = Manager()
