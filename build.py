from setuptools import Extension

def build(setup_kwargs):
    setup_kwargs.update(
        ext_modules = [Extension("app.cython_ext.monopoly", ["app/cython_ext/monopoly.cpp"])]
    )

def cythonize_monopoly():
    try:
        from Cython.Build import cythonize
    except:
        print("Cython is not installed. To install, run `poetry install -E cython`")
        return
    # return cythonize("app/cython_ext/monopoly.pyx", annotate=True)
    # Don't return the result, we don't actually use it and it makes the make
    # think there is an error
    cythonize("app/cython_ext/monopoly.pyx", annotate=True)
