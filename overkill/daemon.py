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
