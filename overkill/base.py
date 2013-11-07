from . import manager
from threading import Lock
from .exceptions import NotPublishingError, NoSourceError

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
        source.unsubscribe(self, subscription)

    @manager.queued
    def receive_updates(self, updates, source):
        self.handle_updates(updates, source)
            
    
    def handle_updates(self, updates, source):
        raise NotImplementedError()

    @manager.queued
    def receive_unsubscribe(self, subscription, source):
        self.subscriptions[subscription].remove(source)
        self.handle_unsubscribe(subscription, source)

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
            raise NotPublishingError(self, subscription)
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
            self.on_unsubscribe(subscriber, subscription)
        except KeyError:
            pass

    def push_unsubscribe(self, subscription):
        subscribers = self.subscribers[subscription]
        # Don't just delete this
        # Something else might be relying on the dictionary.
        self.subscribers[subscription] = set()
        for sink in subscribers:
            sink.receive_unsubscribe(subscription, self)

    def is_subscribed(self, subscription):
        return bool(self.subscribers.get(subscription, False))

    def push_updates(self, updates):
        self.published_data.update(updates)
        for subscriber in set().union(
            *(self.subscribers[k] for k in updates if k in self.subscribers)
        ):
            subscriber.receive_updates(updates, self)

