import threading, time, itertools, sys, os

"""
Extremely bareboned version of spinner from yaspin library
https://github.com/pavdmyt/yaspin/tree/master/yaspin
"""
class Spinner(object):
    MAC_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    WINDOWS_FRAMES = ["[    ]","[=   ]","[==  ]","[=== ]","[ ===]","[  ==]",
			         "[   =]","[    ]","[   =]","[  ==]","[ ===]","[====]",
			         "[=== ]","[==  ]","[=   ]"]
    def __init__(self):
        self._frames = self.WINDOWS_FRAMES if os.name == "nt" else self.MAC_FRAMES
        self._interval = 80 * 0.001 # convert from ms to secs
        self._cycle = itertools.cycle(self._frames)
        self.text = ""
        self._stdout_lock = threading.Lock()
        self._stop_spin = None
        self._spin_thread = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if self._spin_thread.is_alive():
            self.stop()
        return False

    def start(self):
        if sys.stdout.isatty():
            self._hide_cursor()
        self._stop_spin = threading.Event()
        self._spin_thread = threading.Thread(target=self._spin)
        self._spin_thread.start()

    def stop(self):
        if self._spin_thread:
            self._stop_spin.set()
            self._spin_thread.join()

            sys.stdout.write(f"\r{self.text}")
            self._clear_line()
            sys.stdout.write("\n")

            if sys.stdout.isatty():
                self._show_cursor()

    def _spin(self):
        while not self._stop_spin.is_set():
            # Compose Output
            spin_phase = next(self._cycle)
            out = f"\r{spin_phase} {self.text}"

            # Write
            with self._stdout_lock:
                sys.stdout.write(out)
                self._clear_line()
                sys.stdout.flush()

            # Wait
            time.sleep(self._interval)

    @staticmethod
    def _hide_cursor():
        if os.name != "nt":
            sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @staticmethod
    def _show_cursor():
        if os.name != "nt":
            sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    @staticmethod
    def _clear_line():
        if os.name == "nt":
            sys.stdout.write(" "*7+"\r")
        else:
            sys.stdout.write("\033[K")

"""
Time how long it takes code to run inside a `Timer` context. Print out the
time when the context is closed.

Example:

with Timer():
    # code to time here

"""
class Timer(object):
    def __init__(self):
        self.start = None

    def __enter__(self):
        self.start = time.monotonic()

    def __exit__(self, exc_type, exc_val, traceback):
        print(f"Run time: {self.format_duration(time.monotonic()-self.start)}")
        return False

    def format_duration(self, duration):
        duration_str = ''
        mins = int(duration / 60)
        if mins > 0:
            duration_str = f"{pluralize(mins,'min')} "
        secs = duration - (mins * 60)
        format = '.0f' if mins > 0 else '.2f'
        duration_str += f"{pluralize(secs,'sec',format)}"
        return duration_str

"""
Given a value and a label for that value, make the label plural if the value is
greater than 1. Can also provide a format string for the value.

Return the value, formatted if necessary, with the correct label.
"""
def pluralize(value, label, format=None):
    value_str = str(value) if format is None else f"{value:{format}}"
    return f"{value_str} {label}{'s' if value != 1 else ''}"
