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

# I like clean scopes and I cannot lie...
def wrapper():
    import pkgutil, sys
    from overkill.sources import Source
    import overkill.extra as package
    self = sys.modules[__name__]
    sources = []

    for imp, name, ispkg in pkgutil.iter_modules(package.__path__, prefix=__package__+"."):
        if ispkg or name == __name__:
            continue
        mod = imp.find_module(name).load_module(name)
        if mod in sys.modules:
            continue
        for k,v in mod.__dict__.items():
            if type(v) is type and issubclass(v, Source):
                setattr(self, k, v)
                sources.append(k)
    return sources

__all__ = wrapper()
del wrapper
