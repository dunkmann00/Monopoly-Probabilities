import os
from multiprocessing import Pool
from itertools import starmap
from monopoly import Monopoly
from utils import Spinner, Timer, pluralize

try:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--turns", help="The number of turns to simulate.", type=int, default=100)
    parser.add_argument("--no-parallel", help="Don't run the simulation in parallel.", action="store_true")
    parser.add_argument("--max-cpu-cores", help="When running in parallel, the maximum number of CPU cores to use for the simulation.", type=int)
    flags = parser.parse_args()
except ImportError:
    flags = None


def generate_games(turns):
    i=0
    while i < len(turns):
        game = Monopoly()
        yield game, turns[i]
        i+=1

"""
Calculate how many games to play and how many turns in each game.
If not running in parallel we only want one game, if we are running in parallel
we will play at most, the same number of games as cpu_count. When dividing the
turns up amonst games, the fewest number of turns in a game is 1,000,000.
"""
def calculate_all_turns(total_turns, cpu_count):
    turns = []
    turns_remaining = total_turns
    turns_per_game = max(1000000, int(total_turns/cpu_count))

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

def play_game(game, turns):
    game.take_turns(turns)
    return game.results

"""
Save the results from the simulation to a txt and a csv file
"""
def save_results(results):
    total_turns = sum(results)
    with open('board-spaces.txt') as fnames:
        with open('board-probabilities.txt', 'w') as fprobs, open('board-probabilities.csv', 'w') as fprobs_csv:
            for i,square_name in enumerate(fnames):
                if i < len(results):
                    fprobs.write(f"{square_name.rstrip():<21} - {results[i]/total_turns:.3%}\n")
                    fprobs_csv.write(f"{square_name.rstrip()},{results[i]/total_turns:.3%}\n")


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
    print(info_text)
    total_turns = sum(results)
    print(f"Complete, {pluralize(total_turns,'move',',')} made")
    save_results(results)


if __name__ == '__main__':
    main()
