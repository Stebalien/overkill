from setuptools import setup, find_packages
setup(
    name = "overkill",
    version = "0.1",
    packages = find_packages(),
    namespace_packages = ["overkill.extra"],
    author = "Steven Allen",
    author_email = "steven@stebalien.com",
    description = "A local pub-sub framework",
    license = "GPL3",
    url = "http://stebalien.com",
    entry_points = {
        'console_scripts': ['overkill = overkill.daemon:run']
    }
)
