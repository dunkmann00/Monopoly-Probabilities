import threading, time, itertools, sys, os
import pygal
from pathlib import Path
import importlib.resources as resources
from collections import namedtuple

from . import data

from .monopoly import Monopoly as PyMonopoly
try:
    from .cython_ext import Monopoly as CMonopoly
except ImportError:
    CMonopoly = None

"""
Extremely bareboned version of spinner from yaspin library
https://github.com/pavdmyt/yaspin/tree/master/yaspin
"""
class Spinner(object):
    MAC_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    WINDOWS_FRAMES = ["[    ]","[=   ]","[==  ]","[=== ]","[ ===]","[  ==]",
			         "[   =]","[    ]","[   =]","[  ==]","[ ===]","[====]",
			         "[=== ]","[==  ]","[=   ]"]
    def __init__(self, text=""):
        self._frames = self.WINDOWS_FRAMES if os.name == "nt" else self.MAC_FRAMES
        self._interval = 80 * 0.001 # convert from ms to secs
        self._cycle = itertools.cycle(self._frames)
        self.text = text
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
        try:
            self._spin_thread.start()
        finally:
            # Ensure cursor is not hidden if any failure occurs that prevents
            # getting it back
            self._show_cursor()

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
            self._stop_spin.wait(self._interval)

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
        self.end = None

    def __enter__(self):
        self.start = time.monotonic()

    def __exit__(self, exc_type, exc_val, traceback):
        self.end = time.monotonic()
        return False

    @property
    def duration(self):
        if self.start is None or self.end is None:
            return None
        return self.end - self.start

BoardSpace = namedtuple("BoardSpace", ["name", "color"])

class Result():
    def __init__(self, results, duration, num_cores_used):
        self.results = results
        self.total_turns = sum(results)
        self.percentages = [result/self.total_turns for result in results]
        self.duration = duration
        self.num_cores_used = num_cores_used

    @property
    def pretty_duration(self):
        if self.duration is None:
            return ''
        duration_str = ''
        mins, secs = divmod(self.duration, 60)
        if mins > 0:
            duration_str = f"{pluralize(mins,'min','.0f')} "
        format = '.0f' if mins > 0 else '.2f'
        duration_str += f"{pluralize(secs,'sec',format)}"
        return duration_str

    @property
    def pretty_total_turns(self):
        return pluralize(self.total_turns,'move',',')

    @property
    def pretty_num_cores_used(self):
        return pluralize(self.num_cores_used, 'cpu core')

"""
Returns either the C extension or pure Python version of the Monopoly class
depending on:
    - What was requested with the `pure_python` argument.
    - If the C extension is requested then it depends if it is available.

* Doing this inside a function also prevents the text that is printed from
  being printed multiple times when run in parallel (with multiprocessing)
"""
def get_monopoly_cls(pure_python=False):
    if pure_python:
        print("-- Using Pure Python Monopoly class --")
        return PyMonopoly
    else:
        if CMonopoly is not None:
            return CMonopoly
        else:
            print("-- Falling back to Pure Python Monopoly class --")
            return PyMonopoly

"""
Returns a generator that yields a tuple containing a new Monopoly object and the
number of turns to simulate for that game.
"""
def generate_games(monopoly_cls, turns):
    i=0
    while i < len(turns):
        game = monopoly_cls()
        yield game, turns[i]
        i+=1
"""
Calls the game's `take_turns` method with the value from `turns`. Then returns
the results list. This is needed as the function that gets passed to starmap.
"""
def play_game(game, turns):
    game.take_turns(turns)
    return game.results

"""
Given a value and a label for that value, make the label plural if the value is
greater than 1. Can also provide a format string for the value.

Return the value, formatted if necessary, with the correct label.
"""
def pluralize(value, label, format=None):
    value_str = str(value) if format is None else f"{value:{format}}"
    return f"{value_str} {label}{'s' if value != 1 else ''}"

"""
Calculate how many games to play and how many turns in each game.
If not running in parallel we only want one game, if we are running in parallel
we will play at most, the same number of games as cpu_count. When dividing the
turns up amonst games, the fewest number of turns in a game is 1,000,000.
"""
def calculate_all_turns(total_turns, cpu_count):
    turns = []
    turns_remaining = total_turns
    turns_per_game = max(1000000, total_turns//cpu_count)

    while len(turns) < cpu_count and turns_remaining > 0:
        game_turns = min(turns_per_game, turns_remaining)
        turns.append(game_turns)
        turns_remaining-=game_turns

    for i in range(len(turns)):
        if turns_remaining == 0:
            break
        turns[i]+=1
        turns_remaining-=1
    return turns

class Bar(pygal.Bar):
    def _compute_margin(self):
        super()._compute_margin()
        self.margin_box.right = 20

class CustomStyle(pygal.style.Style):
    font_family = "verdana, sans-serif"
    plot_background = "white"
    opacity = "1"
    guide_stroke_dasharray = "1,0"
    guide_stroke_color = "#dcdcdc"
    major_guide_stroke_dasharray = guide_stroke_dasharray
    major_guide_stroke_color = guide_stroke_color
    colors = ("black",)
    label_font_size = 20
    major_label_font_size = label_font_size
    title_font_size = 32
    value_font_size = 18
    value_colors = ("black",)
    tooltip_font_size = 29
    foreground = "black"

def make_chart(result, board_spaces):
    config = pygal.Config()
    config.show_legend = False
    config.human_readable = True
    config.title = f"Monopoly Probabilities Results ({result.pretty_total_turns} - {result.pretty_duration} - {result.pretty_num_cores_used})"
    config.x_title = "Board Space Names"
    config.y_title = "Percentage (%) of moves ended on"
    config.x_labels = [board_space.name for board_space in board_spaces]
    config.x_label_rotation = 30
    config.margin_left = 30
    config.value_formatter = lambda y: f"{y:.1%}"
    config.stroke = False
    config.width = 2400
    config.height = 1200
    config.print_values = True
    config.print_values_position = "top"
    custom_css = '''
        {id} .axis.x .guides {{
            transform: translate(-10px, 0px);
        }}
    '''
    # Can't do:
    # config.css.append('inline:' + custom_css) and have it insert the id
    # This is a bug, adding text with inline doesn't add the id
    # https://github.com/Kozea/pygal/blob/4a32a53c691021b864b96f426a8aa339dadee55f/pygal/svg.py#L103-L123
    # Instead of not adding it or using a temporary file, I'm getting the id
    # myself after creating the bar chart and adding it into the 'custom_css'
    # string manually

    chart = Bar(config=config, style=CustomStyle())
    chart.config.css.append('inline:' + custom_css.format(id=f"#chart-{chart.uuid}"))

    values = [{"value": percentage, "color": board_space.color} for percentage, board_space in zip(result.percentages, board_spaces)]
    chart.add('Probabilities', values)

    return chart

"""
Save the results from the simulation to a txt and a csv file
"""
def save_results(result, results_dir=None):
    results_dir = results_dir or 'results'
    results_dir = Path(results_dir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    # This should be changed to use the newer 'files()' api, but PyOxidizer
    # doesn't yet support it
    with resources.open_text(data, 'board-spaces.txt') as fp_board_spaces:
        board_spaces = [BoardSpace(*value.rstrip().split(":")) for value in fp_board_spaces]

    print(f"Saving Results to {results_dir}:")

    probs_txt = results_dir / 'board-probabilities.txt'
    probs_csv = results_dir / 'board-probabilities.csv'
    with probs_txt.open('w') as fprobs, probs_csv.open('w') as fprobs_csv:
        for percentage, board_space in zip(result.percentages, board_spaces):
            fprobs.write(f"{board_space.name:<21} - {percentage:.3%}\n")
            fprobs_csv.write(f"{board_space.name},{percentage:.3%}\n")
    print(probs_txt.name)
    print(probs_csv.name)

    chart = make_chart(result, board_spaces)

    probs_svg_chart = results_dir / 'board-probabilities-chart.svg'
    chart.render_to_file(str(probs_svg_chart))
    print(probs_svg_chart.name)

    if not getattr(sys, 'oxidized', False):
        probs_png_chart = results_dir / 'board-probabilities-chart.png'
        chart.render_to_png(str(probs_png_chart))
        print(probs_png_chart.name)
    else:
        print("* Couldn't save .png version of chart, not supported with "
              "PyOxidizer build.")
