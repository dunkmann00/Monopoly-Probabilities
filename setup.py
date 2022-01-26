# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['monopoly', 'monopoly.cython_ext', 'monopoly.data']

package_data = \
{'': ['*']}

entry_points = \
{'console_scripts': ['monopolize = build:cythonize_monopoly',
                     'monopoly = monopoly:main']}

setup_kwargs = {
    'name': 'monopoly-probabilities',
    'version': '0.1.0',
    'description': 'Calculate the probabilties of landing on each different square on a monopoly board.',
    'long_description': None,
    'author': 'George Waters',
    'author_email': 'george@georgeh2os.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<3.11',
}
from build import *
build(setup_kwargs)

setup(**setup_kwargs)
