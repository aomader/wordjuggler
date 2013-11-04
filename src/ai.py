#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import log
from operator import itemgetter
from os.path import join

from common import Player, PROJECT_PATH

DEFAULT_WORDLIST = join(PROJECT_PATH, 'data', 'words.csv')


class BruteForceBot(Player):
    '''
    The interactive interface of our AI. Should react like a normal player.
    '''
    RATE_MINIMUM = 1

    def __init__(self, *args, words=DEFAULT_WORDLIST, **kwargs):
        super().__init__(*args, **kwargs)
        self.words = self.load_words(words)

    def load_words(self, filename):
        ''' Load an initial word list '''
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            return set(word.strip().lower() for word in f if
                    word.strip().isalpha() and word.strip())

    def find_words_in_line(self, game, line):
        ''' Find all possible words in a line representing a boards row '''
        if not line.isspace():
            for word in self.words:
                for i in range(len(line) - len(word), -1, -1):
                    fine = False
                    score = 0
                    rack = self.letters[:]
                    for j in range(0, len(word)):
                        if line[i+j] == ' ':
                            if word[j] not in rack:
                                fine = False
                                break
                            pos = rack.find(word[j])
                            rack = rack[:pos] + rack[pos + 1:]
                            score += game.letters.get_score(word[j])
                        elif word[j] != line[i+j]:
                            fine = False
                            break
                        else:
                            fine = True
                    if fine and score > 0:
                        yield (i, word, score)

    def find_all_possible_words(self, game):
        ''' Find all possible words '''
        for direction,lines in (('right', game.board.get_rows()),
                                ('down', game.board.get_columns())):
            lines = (''.join(l.char if l else ' ' for l in line)
                     for line in lines)
            for i,line in enumerate(lines):
                for j,word,score in self.find_words_in_line(game, line):
                    yield (j, i, direction, word) if direction == \
                          'right' else (i, j, direction, word)

    def find_all_cross_words(self, game, word):
        ''' Find all cross words which would be created by word '''
        # TODO: THERE HAS TO BE A BETTER SOLUTION !!
        x,y,direction,word = word
        length = len(word)
        width = game.width
        if direction == 'down':
            get_letter = lambda dx, dy: game.board.get_letter(dy, dx)
            width = game.height
            tmp = y
            y = x
            x = tmp
        else:
            get_letter = game.board.get_letter

        if (x - 1 >= 0 and get_letter(x-1, y)) or \
           (x + length < width and get_letter(x+length, y)):
            cross = ''
            for i in range(x - 1, -1, -1):
                letter = get_letter(i, y)
                if not letter:
                    break
                cross = letter.char + cross
            cross = cross + word
            for i in range(x + length, width):
                letter = get_letter(i, y)
                if not letter:
                    break
                cross = cross + letter.char
            yield cross

        yd = y - 1
        yi = y + 1

        for i,c in enumerate(word):
            xi = x + i
            if (yd >= 0 and get_letter(xi, yd)) or \
               (yi < width and get_letter(xi, yi)):
                cross = ''
                for i in range(yd, -1, -1):
                    letter = get_letter(xi, i)
                    if not letter:
                        break
                    cross = letter.char + cross
                cross = cross + c
                for i in range(yi, width):
                    letter = get_letter(xi, i)
                    if not letter:
                        break
                    cross = cross + letter.char
                yield cross

    def find_all_words(self, game):
        ''' Find all valid words sorted by score '''
        return (word for word in self.find_all_possible_words(game)
                if all(cross in self.words for cross in
                       self.find_all_cross_words(game, word)))

    def find_initial_words(self, game):
        ''' Find all words which would be valid first words '''
        for word in self.words:
            length = len(word)
            if length > min(7, max(game.width, game.height)):
                continue
            rack = self.letters[:]
            valid = True
            for c in word:
                if c not in rack:
                    valid = False
                    break
                pos = rack.index(c)
                rack = rack[:pos] + rack[pos+1:]
            if valid:
                if length <= game.width:
                    x = int((game.width - length) / 2)
                    y = int(game.height / 2)
                    direction = 'right'
                else:
                    x = int(game.width / 2)
                    y = int((game.height - length) / 2)
                    direction = 'down'
                yield (x, y, direction, word)

    def rate_word(self, word):
        ''' Try to rate a word '''
        score = self.game.board.get_word_score(self.game.letters, *word)

        rack = self.letters[:]
        for c in word[3]:
            pos = rack.find(c)
            if pos > -1:
                rack = rack[:pos] + rack[pos + 1:]

        total = len(rack)
        vocals = sum(rack.count(c) for c in 'aeiou')
        consonant = total - vocals

        if consonant == 0 or vocals == 0:
            vc_entropy = 0
        elif consonant == vocals:
            vc_entropy = 0
        else:
            vc_entropy = abs(vocals/total * log(vocals/total, 2) +
                             consonant/total * log(consonant/total, 2))


        rate = score * (vc_entropy + (self.game.rack_size - total)/7)

        return rate


    def exchange(self):
        ''' Exchange letters the best way '''
        vocals = sum(self.letters.count(c) for c in 'aeiou')
        consonants = len(self.letters) - vocals
        letters = ''

        for c in self.letters:
            if c in ('aeiou') and vocals > 2:
                letters += c
                vocals -= 1
            elif c not in ('aeiou'):
                letters += c
        
        return self.exchange_letters(letters)


    def play(self):
        ''' Try to find the best possible move ... '''
        current_words = list(self.game.board.get_words())
        last_moves = self.game.moves[-3:]
        ranking = sorted(((p.score - sum(self.game.letters.get_score(c)
                                          for c in p.letters) if p == self
                                      else 7, p) for p
                           in self.game.players), key=itemgetter(0),
                          reverse=True)

        # Add new words
        self.words.update(word[3] for word in current_words)

        # Do we win by passing?
        if len(last_moves) == 3 and all(m[0] != Player.PLACE_WORD for _,m
                                        in last_moves) and \
           ranking[0][1] == self and ranking[0][0] > ranking[1][0]:
            return self.skip()

        # Not the first word
        if current_words:
            # Find all valid words
            words = self.find_all_words(self.game)
        else:
            # Find all valid initial words
            words = self.find_initial_words(self.game)

        words = sorted(list(filter(lambda x: self.rate_word(x) > self.RATE_MINIMUM,
                              words)), key=self.rate_word, reverse=True)

        if words:
            return self.place_word(*words[0])

        return self.exchange()


# vim: set expandtab shiftwidth=4 softtabstop=4 textwidth=79:
