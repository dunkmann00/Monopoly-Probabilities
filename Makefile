PYINSTALLER_BUILD_DIR = pyinstaller-build
PYOXIDIZER_BUILD_DIR = pyoxidizer-build
NUITKA_BUILD_DIR = nuitka-build

PYTHON = python3

BUILD_PIP_CMD = pip install -e .
ifdef CYTHON
BUILD_PIP_CMD := $(BUILD_PIP_CMD)[cython]
endif

.PHONY: help build install remove clean monopolize pyinstaller pyoxidizer nuitka all-binaries

help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  build        build monopoly-probabilites so it can be run with python"
	@echo "  install      install dependencies necessary for building binaries"
	@echo "  remove       remove the virtual environment"
	@echo "  clean        remove files & folders from building binaries, etc."
	@echo "  monopolize   run cythonize command on monopoly.pyx"
	@echo "  pyinstaller  build pyinstaller binary"
	@echo "  pyoxidizer   build pyoxidizer binary"
	@echo "  nuitka       build nuitka binary"
	@echo "  all-binaries build all of the binaries"

build:
	@echo "--- Build monopoly-probabilties with pip in venv ---"
	@echo "--- This allows monopoly-probabilities to be run locally with"
	@echo "    Python. ---"
	$(PYTHON) -m venv venv
	. venv/bin/activate; $(BUILD_PIP_CMD)
	@echo "--- Done ---"

install:
	@echo "--- Install monopoly-probabilties dependencies with pip into venv ---"
	@echo "--- This is needed to build binaries of monopoly-probabilties. ---"
	$(PYTHON) -m venv venv
	. venv/bin/activate; pip install -r bin-requirements.txt
	@echo "--- Done ---"

remove:
	rm -rf venv/

clean:
	@echo "--- Removing build artifacts. ---"
	rm -rf build/
	rm -rf dist/
	rm -rf $(PYINSTALLER_BUILD_DIR)/
	rm -f monopoly.spec
	rm -rf $(PYOXIDIZER_BUILD_DIR)/
	rm -rf monopoly_probabilities.egg-info/
	rm -rf $(NUITKA_BUILD_DIR)/
	@echo "--- Done ---"

monopolize:
	@echo "--- Running cythonize on monopoly.pyx file. ---"
	monopolize
	@echo "--- Done ---"

pyinstaller:
	@echo "--- Building Package with PyInstaller. ---"
	rm -rf dist/pyinstaller/
	$(PYTHON) setup.py build --build-lib $(PYINSTALLER_BUILD_DIR)
	cp -f monopoly.py $(PYINSTALLER_BUILD_DIR)
	@echo "--- Done ---"
	@echo "--- Creating PyInstaller single file executable. ---"
	pyinstaller $(PYINSTALLER_BUILD_DIR)/monopoly.py \
				--add-data $(PYINSTALLER_BUILD_DIR)/app/data/:app/data \
				--distpath dist/pyinstaller/ -F
	@echo "--- Done. File can be found in dist/ ---"

pyoxidizer:
	@echo "--- Building Package with PyOxidizer. ---"
	rm -rf dist/pyoxidizer/
	pyoxidizer build --release --var PYOXIDIZER_BUILD_DIR $(PYOXIDIZER_BUILD_DIR)
	@echo "--- Done. Copying package files into dist/ ---"
	mkdir -p dist/pyoxidizer/
	cp -rf $(PYOXIDIZER_BUILD_DIR)/*/release/install/ dist/pyoxidizer/
	@echo "--- Done. Files can be found in dist/ ---"

nuitka:
	@echo "--- Building Package with Nuitka. ---"
	rm -rf dist/nuitka/
	$(PYTHON) setup.py build --build-lib $(NUITKA_BUILD_DIR)
	cp -f monopoly.py $(NUITKA_BUILD_DIR)
	@echo "--- Done ---"
	@echo "--- Creating Nuitka single file executable. ---"
	$(PYTHON) -m nuitka --enable-plugin=multiprocessing \
						--onefile \
						--include-data-file $(NUITKA_BUILD_DIR)/app/data/*.txt=app/data/ \
						--output-dir $(NUITKA_BUILD_DIR)/build \
						-o dist/nuitka/monopoly \
						$(NUITKA_BUILD_DIR)/monopoly.py
	@echo "--- Done. Files can be found in dist/ ---"

all-binaries: pyinstaller pyoxidizer nuitka
