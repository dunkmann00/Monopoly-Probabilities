# cython: language_level=3


import random

cdef class Monopoly():
    cdef int num_spaces # = 40
    cdef set community_squares # = {2,17,33} # this is correct, but differs from maths.py  # THIS IS WHERE THE DESCREPANCY
    cdef set chance_squares # = {7,22,36} # this is correct, but differs from maths.py     # IN PROBABILITIES COMES FROM
    cdef list community_cards # = [0,-1] + [None for i in range(14)] # Two cards change your position, the rest don't matter
    cdef list chance_cards # = [0,5,11,24,39,'U','R','B',-1] + [None for i in range(7)] # 9 cards change your position
    cdef list roll_values # = [2,3,4,5,6,7,3,4,5,6,7,8,4,5,6,7,8,9,5,6,7,8,9,10,6,7,8,9,10,11,7,8,9,10,11,12] # all possible combos of dice rolls

    cdef list community_deck
    cdef list chance_deck
    cdef public list results
    cdef int total_turns
    cdef int current_position
    cdef int doubles
                                                                                                  # more efficient than rolling dice twice
    def __init__(self):
        self.num_spaces = 40
        self.community_squares = {2,17,33}
        self.chance_squares = {7,22,36}
        self.community_cards = [0,-1] + [None for i in range(14)]
        self.chance_cards = [0,5,11,24,39,'U','R','B',-1] + [None for i in range(7)]
        self.roll_values = [2,3,4,5,6,7,3,4,5,6,7,8,4,5,6,7,8,9,5,6,7,8,9,10,6,7,8,9,10,11,7,8,9,10,11,12]

        self.community_deck = []
        self.chance_deck = []
        self.results = [0]*(self.num_spaces+1) # +1 because we are counting jail vs visiting separately
        self.total_turns = 0
        self.current_position = 0
        self.doubles = 0

    def take_turns(self, turns):
        while self.total_turns < turns:
            spaces, double = self.roll_dice()
            if double:
                self.doubles+=1
            else:
                self.doubles = 0
            if self.doubles == 3:
                self.move_to(-1)
                self.doubles = 0 # reset after 3 doubles (differs from maths.py)
            else:
                self.move_spaces(spaces)
                if self.current_position == 30: # Go to Jail
                    self.move_to(-1)
                elif self.current_position in self.community_squares:
                    self.draw_community_chest()
                elif self.current_position in self.chance_squares:
                    self.draw_chance()
            self.end_turn()

    def roll_dice(self):
        # roll_index = random.randrange(36) # This seems to take a little longer
        roll_index = int(random.random()*36)
        return self.roll_values[roll_index], roll_index in {0,7,14,21,28,35}

    def move_spaces(self, spaces):
        if self.current_position == -1: # We are in jail, move us to just visiting
            self.current_position = 10
        self.current_position = (self.current_position+spaces) % self.num_spaces

    def move_to(self, square):
        self.current_position = square

    def end_turn(self):
        self.results[self.current_position]+=1
        self.total_turns+=1

    def move_to_utility(self):
        if self.current_position > 12 and self.current_position < 28:
            self.move_to(28)
        else:
            self.move_to(12)

    def move_to_railroad(self):
        distance_rr = (self.current_position+5)%10
        if distance_rr != 0:
            distance_rr = 10-distance_rr
        self.move_spaces(distance_rr)

    def draw_community_chest(self):
        if len(self.community_deck) == 0:
            self.community_deck = random.sample(self.community_cards, len(self.community_cards))
        card = self.community_deck.pop()
        if card is not None:
            self.move_to(card)

    def draw_chance(self):
        if len(self.chance_deck) == 0:
            self.chance_deck = random.sample(self.chance_cards, len(self.chance_cards))
        card = self.chance_deck.pop()
        if card == 'U':
            self.move_to_utility()
        elif card == 'R':
            self.move_to_railroad()
        elif card == 'B':
            self.move_spaces(-3)
        elif card is not None:
            self.move_to(card)
