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

class NotPublishingError(Exception):
    def __init__(self, source, subscription, subscriber):
        self.source = source
        self.subscription = subscription
        super().__init__(f"{self.source.__class__.__name__} not publishing '{self.subscription}'"
                         f" (requested by {subscriber})")

class NoSourceError(Exception):
    def __init__(self, source, subscription):
        self.source = source
        self.subscription = subscription
        super().__init__(f"{self.source.__class__.__name__} not publishing '{self.subscription}'")
