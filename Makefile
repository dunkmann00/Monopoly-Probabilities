PYINSTALLER_BUILD_DIR = pyinstaller-build

all:
	@echo "\nThere is no default Makefile target right now. Try:\n"

monopolize:
	@echo "Running cythonize on monopoly.pyx file."
	@poetry run monopolize
	@echo "Done"

pyinstaller:
	@echo "Building Package."
	@poetry run python setup.py build --build-lib $(PYINSTALLER_BUILD_DIR)
	@cp -f monopoly.py $(PYINSTALLER_BUILD_DIR)
	@echo "Done"
	@echo "Creating PyInstaller single file executable."
	@poetry run pyinstaller $(PYINSTALLER_BUILD_DIR)/monopoly.py --add-data $(PYINSTALLER_BUILD_DIR)/app/data/:app/data -F
	@echo "Done. File can be found in dist/"

clean:
	@echo "Removing Build artifacts."
	rm -rf build/
	rm -rf dist/
	rm -rf $(PYINSTALLER_BUILD_DIR)/
	rm -f monopoly.spec
	@echo "Done"
