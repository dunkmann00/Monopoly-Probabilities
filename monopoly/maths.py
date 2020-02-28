
"""
This is the version from the YouTube video by standupmaths. I have just added
some code to more easily initiate it and see the results.
"""

from utils import Timer

def monop(finish_order=6,games_order=3):
    global turns
    finish = 10**finish_order
    games = 10**games_order

    import random
    from random import shuffle

    squares = []

    while len(squares) < 40:
        squares.append(0)

    # roll values are values from a six by six grid for all dice rolls
    rollvalues = [2,3,4,5,6,7,3,4,5,6,7,8,4,5,6,7,8,9,5,6,7,8,9,10,6,7,8,9,10,11,7,8,9,10,11,12]

    games_finished = 0

    while games_finished < games:

        master_chest = [0,40,40,40,40,10,40,40,40,40,40,40,40,40,40,40]
        chest = [i for i in master_chest]
        shuffle(chest)

        master_chance = [0,24,11,'U','R',40,40,'B',10,40,40,5,39,40,40,40]
        chance = [i for i in master_chance]
        shuffle(chance)

        doubles = 0

        position = 0

        gos = 0

        while gos < finish:

            diceroll = int(36*random.random())

            if diceroll in [0,7,14,21,28,35]:    # these are the dice index values for double rolls
                doubles += 1
            else:
                doubles = 0
            if doubles >= 3:
                position = 10
            else:

                position = (position + rollvalues[diceroll])%40

                if position in [7,22,33]:  # Chance
                    chance_card = chance.pop(0)
                    if len(chance) == 0:
                        chance = [i for i in master_chance]
                        shuffle(chance)
                    if chance_card != 40:

                        if isinstance(chance_card,int):
                            position = chance_card
                        elif chance_card == 'U':
                            while position not in [12,28]:
                                position = (position + 1)%40
                        elif chance_card == 'R':
                            while position not in [5,15,25,35]:
                                position = (position + 1)%40
                        elif chance_card == 'B':
                            position = position - 3

                elif position in [2,17]:  # Community Chest
                    chest_card = chest.pop(0)
                    if len(chest) == 0:
                        chest = [i for i in master_chest]
                        shuffle(chest)
                    if chest_card != 40:
                        position = chest_card

                if position == 30: # Go to jail
                    position = 10


            squares.insert(position,(squares.pop(position)+1))

            gos += 1

        games_finished += 1


    return squares

def main():
    with Timer():
        squares = monop(finish_order=0, games_order=0)
        # squares = monop(finish_order=6, games_order=2)
    turns = sum(squares)
    print(f"Complete, {turns:,} moves made")
    with open('../data/board-spaces.txt') as fnames:
        with open('../results/board-probabilities.txt', 'w') as fprobs, open('../results/board-probabilities.csv', 'w') as fprobs_csv:
            for i,square_name in enumerate(fnames):
                if i < len(squares):
                    fprobs.write(f"{square_name.rstrip():<21} - {squares[i]/turns:.3%}\n")
                    fprobs_csv.write(f"{square_name.rstrip()},{squares[i]/turns:.3%}\n")

if __name__ == '__main__':
    main()
