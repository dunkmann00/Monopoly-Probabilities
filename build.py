from setuptools import Extension
import os

def build(setup_kwargs):
    if os.getenv("BUILD_EXTENSION"):
        setup_kwargs.update(
            ext_modules = [Extension("app.cython_ext.monopoly", ["app/cython_ext/monopoly.cpp"])]
        )
