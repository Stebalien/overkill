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

from setuptools import setup, find_packages
setup(
    name = "overkill",
    version = "0.1",
    packages = find_packages(),
    namespace_packages = ["overkill.extra"],
    author = "Steven Allen",
    author_email = "steven@stebalien.com",
    description = "A local pub-sub framework",
    license = "GPLV3",
    url = "http://stebalien.com",
    entry_points = {
        'console_scripts': ['overkill = overkill.daemon:run']
    }
)
