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

from . import manager
from threading import Lock
from .exceptions import NotPublishingError, NoSourceError
import subprocess, os
from time import time

__all__=("Runnable", "Subscriber", "Publisher")



class Runnable:
    def __init__(self, *args, **kwargs):
        self.running = False
        self._state_lock = Lock()
        super().__init__(*args, **kwargs)

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def start(self, *args, **kwargs):
        with self._state_lock:
            if self.running:
                return False
            else:
                self.running = True
        self.on_start()
        return True

    def stop(self, *args, **kwargs):
        with self._state_lock:
            if not self.running:
                return False
            else:
                self.running = False
        self.on_stop()
        return True

class Subscriber:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriptions = {}

    def subscribe_to(self, subscription, source=None):
        if source is None:
            if manager.aggregator:
                source = manager.aggregator
            else:
                raise NoSourceError()
        self.subscriptions.setdefault(subscription, set()).add(source)
        source.subscribe(self, subscription)

    def unsubscribe_from(self, subscription, source=None):
        if source is None:
            if manager.aggregator:
                source = manager.aggregator
            else:
                raise NoSourceError()
        self.subscriptions[subscription].remove(source)
        if not self.subscriptions[subscription]:
            del self.subscriptions[subscription]
        source.unsubscribe(self, subscription)

    @manager.queued
    def receive_updates(self, updates, source):
        self.handle_updates(updates, source)
            
    
    def handle_updates(self, updates, source):
        raise NotImplementedError()

    @manager.queued
    def receive_unsubscribe(self, subscription, source):
        try:
            self.subscriptions[subscription].remove(source)
        except KeyError:
            return False
        if not self.subscriptions[subscription]:
            del self.subscriptions[subscription]
        self.handle_unsubscribe(subscription, source)
        return True

    def handle_unsubscribe(self, subscription, source):
        raise NotImplementedError("%s, %s" % (self, subscription))

class Publisher:
    publishes = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribers = {}
        self.published_data = {}

    def get(self, *args, **kwargs):
        return self.published_data.get(*args, **kwargs)

    def is_publishing(self, subscription):
        return self._can_publish() and subscription in self.publishes

    def _can_publish(self):
        return True

    @manager.queued
    def subscribe(self, subscriber, subscription):
        if not self.is_publishing(subscription):
            raise NotPublishingError(self, subscription, subscriber)
        self.subscribers.setdefault(subscription, set()).add(subscriber)
        if subscription in self.published_data:
            subscriber.receive_updates(self.published_data, self)
        self.on_subscribe(subscriber, subscription)

    def on_subscribe(self, subscriber, subscription):
        pass
    
    def on_unsubscribe(self, subscriber, subscription):
        pass

    @manager.queued
    def unsubscribe(self, subscriber, subscription):
        try:
            self.subscribers[subscription].remove(subscriber)
            if not self.subscribers[subscription]:
                del self.subscribers[subscription]
            self.on_unsubscribe(subscriber, subscription)
        except KeyError:
            pass

    def push_unsubscribe(self, subscription):
        try:
            subscribers = self.subscribers.pop(subscription)
        except KeyError:
            return
        for sink in subscribers:
            sink.receive_unsubscribe(subscription, self)

    def is_subscribed(self, subscription):
        return subscription in self.subscribers

    def push_updates(self, updates):
        self.published_data.update(updates)
        for subscriber in set().union(
            *(self.subscribers[k] for k in updates if k in self.subscribers)
        ):
            subscriber.receive_updates(updates, self)

class Subprocess(Runnable):
    cmd = None
    proc = None
    restart = False
    max_restarts = 5
    start_limit_interval = 10
    
    stdout=stderr=open(os.devnull, 'wb')
    stdin=None

    def start(self):
        if super().start():
            self._restarts = 0
            self._last_restart = time()//1000
            return self._start_subprocess()
        return False

    def _maybe_restart(self):
        if self.running and self.restart:
            now = time()//1000
            self._restarts -= min(
                (self._restarts//self.start_limit_interval)*(now - self._last_restart),
                self._restarts
            )
            self._last_restart = now
            if (self._restarts//self.start_limit_interval) < self.max_restarts:
                self._restarts += self.start_limit_interval
                return self._start_subprocess()
        return False

    def _start_subprocess(self):
        with self._state_lock:
            try:
                if not (self.proc and self.proc.poll() is None):
                    self.proc = subprocess.Popen(self.cmd, stderr=self.stderr, stdout=self.stdout, stdin=self.stdin)
            except:
                return False
            return True

    def stop(self):
        if super().stop():
            try:
                self.proc.terminate()
            except:
                pass
            return True
        return False

    def restart(self):
        if not self.running:
            return
        try:
            self.proc.termintate()
        except:
            pass
        self._start_subprocess()

    def wait(self):
        with self._state_lock:
            if not self.running:
                raise RuntimeError("Not Running")
            self.proc.wait()
