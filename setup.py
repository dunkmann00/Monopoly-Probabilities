# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import Extension
import os

packages = \
['app', 'app.cython_ext', 'app.data']

package_data = \
{'': ['*']}

install_requires = \
['cairosvg @ '
 'https://github.com/dunkmann00/CairoSVG/archive/refs/heads/freeze.zip',
 'pygal>=3.0.0,<4.0.0']

extras_require = \
{'cython': ['cython>=0.29.15,<0.30.0'],
 'nuitka': ['Nuitka @ '
            'https://github.com/Nuitka/Nuitka/archive/40931e2f1c7f63364a82ac77238fed1fc4fd5a2f.zip',
            'zstandard>=0.18.0,<0.19.0',
            'ordered-set>=4.1.0,<5.0.0'],
 'pyinstaller': ['pyinstaller>=5.0,<6.0'],
 'pyoxidizer': ['pyoxidizer>=0.22.0,<0.23.0']}

entry_points = \
{'console_scripts': ['monopoly = app:main',
                     'scriptopoly = scripts:scriptopoly.main']}

setup_kwargs = {
    'name': 'monopoly-probabilities',
    'version': '0.2.0',
    'description': 'Calculate the probabilties of landing on each different square on a monopoly board.',
    'long_description': 'None',
    'author': 'George Waters',
    'author_email': 'george@georgeh2os.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<3.11',
}

if os.getenv("BUILD_EXTENSION"):
    setup_kwargs.update(
        ext_modules = [Extension("app.cython_ext.monopoly", ["app/cython_ext/monopoly.cpp"])]
    )

setup(**setup_kwargs)
