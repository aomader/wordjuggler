#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from sys import argv

from PyQt4.QtGui import QApplication

from ai import BruteForceBot, DEFAULT_WORDLIST
from common import Game, DEFAULT_LETTERSET
from ui import Window, Human


def run():
    parser = ArgumentParser(description='Scrabble game including an AI.')
    parser.add_argument('players', metavar='PLAYER', type=str, nargs='+',
                        help='A player like "TYPE:NAME", valid types are:' +
                             ' bot, human')
    parser.add_argument('-r', '--rows', type=int, default=11, dest='rows',
                        help='Board rows (default: 11)')
    parser.add_argument('-c', '--columns', type=int, default=11,
                        dest='columns', help='Board columns (default: 11)')
    parser.add_argument('-s', '--rack', type=int, default=7, dest='rack',
                        help='Rack size (default: 7)')
    parser.add_argument('-w', '--words', type=str, default=DEFAULT_WORDLIST,
                        dest='words', help='Bot words file (default: %s)' %
                                           DEFAULT_WORDLIST)
    parser.add_argument('-l', '--letters', type=str, default=DEFAULT_LETTERSET,
                        dest='letters', help='Letter-set file (default: %s)' %
                                             DEFAULT_LETTERSET)

    args = parser.parse_args()

    game = Game(args.rows, args.columns, args.rack, args.letters)

    for player in args.players:
        typ,name = player.split(':')
        game.add_player(BruteForceBot(name, game, words=args.words)
                        if typ.lower() == 'bot' else
                        Human(name, game))

    app = QApplication(argv)
    win = Window(game)
    app.exec_()

if __name__ == '__main__':
    run()

# vim: set expandtab shiftwidth=4 softtabstop=4 textwidth=79:
