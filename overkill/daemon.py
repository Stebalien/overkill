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

__all__=("run",)

def run():
    import os.path
    from glob import glob
    from xdg.BaseDirectory import xdg_config_home

    for fp in glob(os.path.join(xdg_config_home, "overkill/*.py")):
        with open(fp) as f:
            exec(f.read(), {})

    manager.run()
