import os
from multiprocessing import Pool
from itertools import starmap
from utils import (Spinner, Timer, pluralize, calculate_all_turns,
                   save_results, generate_games, play_game)

try:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--turns", help="The number of turns to simulate.", type=int, default=100)
    parser.add_argument("--no-parallel", help="Don't run the simulation in parallel.", action="store_true")
    parser.add_argument("--max-cpu-cores", help="When running in parallel, the maximum number of CPU cores to use for the simulation.", type=int)
    flags = parser.parse_args()
except ImportError:
    flags = None

def main():
    with Timer():
        # determine the number of cores to use
        if flags.no_parallel:
            cpu_count = 1
        else:
            cpu_count = min(flags.max_cpu_cores, os.cpu_count()) if flags.max_cpu_cores else os.cpu_count()

        turns = calculate_all_turns(flags.turns, cpu_count)
        info_text = f"Using {pluralize(len(turns),'core')} to simulate {pluralize(sum(turns),'move',',')}"
        with Spinner() as spinner:
            spinner.text = info_text
            if len(turns) <= 1:
                results = [sum(square) for square in zip(*starmap(play_game, generate_games(turns)))]
            else:
                with Pool() as pool:
                    results = [sum(square) for square in zip(*pool.starmap(play_game, generate_games(turns)))]
    total_turns = sum(results)
    print(f"Complete, {pluralize(total_turns,'move',',')} made")
    save_results(results)
