import os, time
from multiprocessing import Pool
from itertools import starmap
from .utils import (Timer, Result, pluralize, init_worker, cancel_on_kbinterrupt,
                    calculate_all_turns, save_results, get_monopoly_cls,
                    generate_games, play_game, console)

from rich.panel import Panel
from rich.text import Text
from rich import box

SPINNER = 'bouncingBar' if os.name == 'nt' else 'dots'

# This is needed to turn off multiprocessing when built with Nuitka.
# No matter what I tried I couldn't get it to work. Hopefully I can fix
# this in the future. If wanting to experiment, set the environment variable
# FORCE_NUITKA_MULTI to try multiprocessing with Nuitka.
NUITKA_BUILD = '__compiled__' in globals()
if os.getenv("FORCE_NUITKA_MULTI"):
    NUITKA_BUILD = False

# Need to put this in a function in order for multiprocessing to work
# when using PyInstaller
def parse_args():
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--turns", help="The number of turns to simulate.", type=int, default=100)
        parser.add_argument("--no-parallel", help="Don't run the simulation in parallel.", action="store_true")
        parser.add_argument("--max-cpu-cores", help="When running in parallel, the maximum number of CPU cores to use for the simulation.", type=int)
        parser.add_argument("--pure-python", help="Use the pure python version for the simulation.", action="store_true")
        parser.add_argument("--results-dir", help="The directory to store the results from the simulation. (Default: 'results')")
        flags = parser.parse_args()
    except ImportError:
        flags = None
    return flags

def pyoxidizer_main():
    from multiprocessing import freeze_support
    freeze_support()
    main()

def main():
    flags = parse_args()

    title = Text(r"""    ___  ___                              _
    |  \/  |                             | |            ____
    | .  . | ___  _ __   ___  _ __   ___ | |_   _      /\' .\    _____
    | |\/| |/ _ \| '_ \ / _ \| '_ \ / _ \| | | | |    /: \___\  / .  /\
    | |  | | (_) | | | | (_) | |_) | (_) | | |_| |    \' / . / /____/..\
    \_|  |_/\___/|_| |_|\___/| .__/ \___/|_|\__, |     \/___/  \'  '\  /
                             | |             __/ |              \'__'\/
                             |_|            |___/
    ______          _           _     _ _ _ _   _
    | ___ \        | |         | |   (_) (_) | (_)
    | |_/ / __ ___ | |__   __ _| |__  _| |_| |_ _  ___  ___
    |  __/ '__/ _ \| '_ \ / _` | '_ \| | | | __| |/ _ \/ __|
    | |  | | | (_) | |_) | (_| | |_) | | | | |_| |  __/\__ \
    \_|  |_|  \___/|_.__/ \__,_|_.__/|_|_|_|\__|_|\___||___/
""",)
    console.print(Panel(title, box=box.DOUBLE_EDGE, border_style="red"), style="bold white")
    print()
    timer = Timer()
    num_cores_used = 0
    with timer:
        # determine the number of cores to use
        if flags.no_parallel:
            cpu_count = 1
        else:
            cpu_count = min(flags.max_cpu_cores, os.cpu_count()) if flags.max_cpu_cores else os.cpu_count()

        if NUITKA_BUILD: # Built with Nuitka, multiprocessing does not work, don't use it
            if cpu_count > 1:
                console.print("Multi-core support is not currently available with the Nuitka build.", style="yellow")
                console.print("Running in single core mode.", style="yellow")
                cpu_count = 1

        monopoly_cls = get_monopoly_cls(pure_python=flags.pure_python)
        turns = calculate_all_turns(flags.turns, cpu_count)
        num_cores_used = len(turns)
        info_template = f"Using [{{color}}]{pluralize(num_cores_used,'core',highlight=True)}[/] to simulate [{{color}}]{pluralize(sum(turns),'move',',',True)}[/]"
        info_text = info_template.format(color="green")
        cancelled_text = info_template.format(color="red") + "[white]...[/][bold red]Cancelled"
        with cancel_on_kbinterrupt(cancelled_text), console.status(info_text, spinner=SPINNER) as console_status:
            if len(turns) <= 1 or NUITKA_BUILD:
                results = [sum(square) for square in zip(*starmap(play_game, generate_games(monopoly_cls, turns)))]
            else:
                with Pool(initializer=init_worker) as pool:
                    processing = pool.starmap_async(play_game, generate_games(monopoly_cls, turns))
                    while not processing.ready():
                        time.sleep(0.1)
                    results = [sum(square) for square in zip(*processing.get())]

    result = Result(results, timer.duration, num_cores_used)
    console.rule("[bold]Results")
    print()
    console.print(f"# of Cores: {num_cores_used}")
    console.print(f"  Run time: [cyan]{result.pretty_duration()}")
    console.print(f"     Moves: [cyan]{result.pretty_total_turns()}")
    save_results(result, flags.results_dir)
