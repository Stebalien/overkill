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
