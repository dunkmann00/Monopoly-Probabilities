import os
from multiprocessing import Pool
from itertools import starmap
from .utils import (Spinner, Timer, pluralize, calculate_all_turns,
                    save_results, generate_games, play_game)

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
        flags = parser.parse_args()
    except ImportError:
        flags = None
    return flags

def main():
    flags = parse_args()
    with Timer():
        # determine the number of cores to use
        if flags.no_parallel:
            cpu_count = 1
        else:
            cpu_count = min(flags.max_cpu_cores, os.cpu_count()) if flags.max_cpu_cores else os.cpu_count()

        if NUITKA_BUILD: # Built with Nuitka, multiprocessing does not work, don't use it
            if cpu_count > 1:
                print("Multi-core support is not currently available with the Nuitka build.")
                print("Running in single core mode.")
                cpu_count = 1

        turns = calculate_all_turns(flags.turns, cpu_count)
        info_text = f"Using {pluralize(len(turns),'core')} to simulate {pluralize(sum(turns),'move',',')}"
        with Spinner(info_text) as spinner:
            if NUITKA_BUILD:
                results = [sum(square) for square in zip(*starmap(play_game, generate_games(turns)))]
            else:
                with Pool() as pool:
                    results = [sum(square) for square in zip(*pool.starmap(play_game, generate_games(turns)))]

    total_turns = sum(results)
    print(f"Complete, {pluralize(total_turns,'move',',')} made")
    save_results(results)
