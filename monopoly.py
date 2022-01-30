import app
from multiprocessing import freeze_support

# This file is only needed as an entry point for PyInstaller/Nuitka

if __name__ == '__main__':
    freeze_support() # Needed for PyInstaller
    app.main()
