from setuptools import Extension

def build(setup_kwargs):
    setup_kwargs.update(
        ext_modules = [Extension("monopoly.cython_ext.monopoly", ["monopoly/cython_ext/monopoly.cpp"])]
    )

def cythonize_monopoly():
    try:
        from Cython.Build import cythonize
    except:
        print("Cython is not installed. To install, run `poetry install -E cython`")
        return
    return cythonize("monopoly/cython_ext/monopoly.pyx", annotate=True)
