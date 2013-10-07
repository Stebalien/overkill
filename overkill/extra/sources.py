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
