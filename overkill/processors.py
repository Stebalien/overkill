from .sinks import Sink
from .sources import Source

__all__=("Aggregator",)

class Aggregator(Sink, Source):
    """ A Proxy Class to manage data sources """
    agg = True

    def is_publishing(self, subscription):
        return self.who_publishes(subscription) is not None

    def __init__(self):
        super().__init__()
        self.sources = []

    def who_publishes(self, subscription):
        for source in self.sources:
            if source.is_publishing(subscription):
                return source
        return None

    def on_subscribe(self, subscriber, subscription):
        if subscription not in self.subscriptions:
            self.subscribe_to(subscription, self.who_publishes(subscription))


    def handle_updates(self, updates, source):
        self.push_updates(updates)

    def handle_unsubscribe(self, subscription, source):
        self.push_unsubscribe(subscription);

    def add_source(self, source):
        self.sources.append(source)
