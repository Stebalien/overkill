class NotPublishingError(Exception):
    def __init__(self, source, subscription):
        self.source = source
        self.subscription = subscription
        super().__init__("{} not publishing '{}'".format(self.source.__class__.__name__, self.subscription))

class NoSourceError(Exception):
    def __init__(self, source, subscription):
        self.source = source
        self.subscription = subscription
        super().__init__("{} not publishing '{}'".format(self.source.__class__.__name__, self.subscription))
