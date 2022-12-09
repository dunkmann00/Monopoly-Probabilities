# cython: language_level=3
# distutils: language = c++

from libcpp.set cimport set

from random import random

from cpython.exc cimport PyErr_CheckSignals

cdef enum:
    JAIL = 40

cdef class Monopoly():
    cdef int num_spaces
    cdef set[int] community_squares # this is correct, but differs from maths.py  # THIS IS WHERE THE DESCREPANCY
    cdef set[int] chance_squares # this is correct, but differs from maths.py     # IN PROBABILITIES COMES FROM
    cdef list community_cards # Two cards change your position, the rest don't matter
    cdef list chance_cards # 9 cards change your position
    cdef int[36] roll_values # all possible combos of dice rolls
    cdef set[int] double_indices # more efficient than rolling dice twice
    cdef list community_deck
    cdef list chance_deck
    cdef readonly long long[41] results
    cdef long long total_turns
    cdef int current_position
    cdef int doubles

    def __init__(self):
        self.num_spaces = 40
        self.community_squares = {2,17,33}
        self.chance_squares = {7,22,36}
        self.community_cards = [0,JAIL] + [None for i in range(14)]
        self.chance_cards = [0,5,11,24,39,'U','R','B',JAIL] + [None for i in range(7)]
        self.roll_values = [2,3,4,5,6,7,3,4,5,6,7,8,4,5,6,7,8,9,5,6,7,8,9,10,6,7,8,9,10,11,7,8,9,10,11,12]
        self.double_indices = {0,7,14,21,28,35}

        self.community_deck = []
        self.chance_deck = []
        self.results = [0 for i in range(self.num_spaces+1)] # +1 because we are counting jail vs visiting separately
        self.total_turns = 0
        self.current_position = 0
        self.doubles = 0

    cpdef take_turns(self, long long turns):
        while self.total_turns < turns:
            spaces = self.roll_dice()
            if self.doubles == 3:
                self.move_to(JAIL)
                self.doubles = 0 # reset after 3 doubles (differs from maths.py)
            else:
                self.move_spaces(spaces)
                if self.current_position == 30: # Go to Jail
                    self.move_to(JAIL)
                elif self.community_squares.count(self.current_position) == 1:
                    self.draw_community_chest()
                elif self.chance_squares.count(self.current_position) == 1:
                    self.draw_chance()
            self.end_turn()

    cdef int roll_dice(self):
        # cdef int roll_index = randrange(36) # This seems to take a little longer
        cdef int roll_index = int(random()*36)
        # cdef int roll_index = rand()%36
        if self.double_indices.count(roll_index) == 1:
            self.doubles+=1
        else:
            self.doubles = 0
        return self.roll_values[roll_index]

    cdef move_spaces(self, int spaces):
        if self.current_position == JAIL: # We are in jail, move us to just visiting
            self.current_position = 10
        self.current_position += spaces
        if self.current_position >= self.num_spaces:
            self.current_position -= self.num_spaces

    cdef move_to(self, int square):
        self.current_position = square

    cdef end_turn(self):
        self.results[self.current_position]+=1
        self.total_turns+=1
        if self.total_turns % 100000 == 0:
            PyErr_CheckSignals()
            with nogil:
                pass

    cdef move_to_utility(self):
        if self.current_position > 12 and self.current_position < 28:
            self.move_to(28)
        else:
            self.move_to(12)

    cdef move_to_railroad(self):
        distance_rr = (self.current_position+5)%10
        if distance_rr != 0:
            distance_rr = 10-distance_rr
        self.move_spaces(distance_rr)

    cdef draw_community_chest(self):
        if len(self.community_deck) == 0:
            # self.community_deck = random.sample(self.community_cards, len(self.community_cards))
            self.community_deck = self.shuffle_deck(self.community_cards)
        card = self.community_deck.pop()
        if card is not None:
            self.move_to(card)

    cdef draw_chance(self):
        if len(self.chance_deck) == 0:
            # self.chance_deck = random.sample(self.chance_cards, len(self.chance_cards))
            self.chance_deck = self.shuffle_deck(self.chance_cards)
        card = self.chance_deck.pop()
        if card == 'U':
            self.move_to_utility()
        elif card == 'R':
            self.move_to_railroad()
        elif card == 'B':
            self.move_spaces(-3)
        elif card is not None:
            self.move_to(card)

    cdef list shuffle_deck(self, list deck):
        cdef list shuffled = deck.copy()
        cdef int i,r
        cdef move
        cdef int n = len(shuffled)
        for i in range(n-1,0,-1):
            r = int(random()*i)
            move = shuffled[r]
            shuffled[r] = shuffled[i]
            shuffled[i] = move
        return shuffled
