"""ASCII Art Generation Script


PYTHON LOGO:

The original Python logo was designed by Tim Parkin and is trademarked
by the Python Software Foundation.

An ASCII art version of the logo was designed by Matthew Barber and is
licensed under CC-BY-4.0. Matthew Barber's ASCII version was used as a
reference for the logo I created here. You can find Matthew Barber's
version online at:

    https://ascii.matthewbarber.io/art/python/

ASCII FONT:

The "python powered" text was generated with FIGlet using the Jazmine
font (jazmine.flf). The banner text was then modified to better match
the letter shapes used in the Python logo.
"""
import itertools
from colorama import Fore, Style


def colorize_line(art_line, color_line, color_codes):
    rendered_characters = []
    prev_code = None
    color_codes = dict(color_codes)  # Make a copy.
    if ' ' not in color_codes:
        color_codes[' '] = Style.RESET_ALL

    zipped = itertools.zip_longest(art_line, color_line, fillvalue=' ')
    for character, code in zipped:
        if prev_code != code:
            rendered_characters.append(color_codes[code])
            prev_code = code
        rendered_characters.append(character)

    return ''.join(rendered_characters)



ascii_art = """
           .....                                     8
         d88888888.                               8  8
        8  88888888                .oPYo. o    o o8P 8oPYo. .oPYo. odPYo.
        88888888888                8    8 8    8  8  8    8 8    8 8'  '8
      .......888888                8    8 8    8  8  8    8 8    8 8    8
 ,88888888888888888 ######.        8YooP' 'YooP8  'Y 8    8 'YooP' 8    8
d888888888888888888 #######;       8           8
88888888888888888' ,########       8         oP'                             8
88888888' ,#################                                                 8
V8888888 ##################" .oPYo. .oPYo. o   o   o .oPYo. oPY^'.oPYo. .oPYo8
 ^888888 #################'  8    8 8    8 Y. .P. .P 8oooo8 8    8oooo8 8    8
         ######'''''''       8    8 8    8 'b.d'b.d' 8.     8    8.     8    8
         ###########         8YooP' 'YooP'  'Y' 'Y'  'Yooo' 8    'Yooo' 'YooP'
         ########  #         8
         '########"          8
            '''''
"""


if __name__ == '__main__':
    import argparse
    import pathlib
    import sys


    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--test', action='store_true', help='Run test suite.')
    group.add_argument('--save', metavar='FILE', help='Save ASCII art to file.')

    args = parser.parse_args()


    if args.test == False:
        ##########################
        # Save or print ASCII art.
        ##########################
        if args.save:
            path = pathlib.Path(args.save)
            if path.exists():
                sys.exit(f'Cannot save: {path} already exists')  # <- EXIT!

            # Save ASCII art to a text file.
            with open(path, 'w') as fh:
                fh.write(ascii_art)
            print(f'ASCII art saved to {path}')

        else:
            # Print the ASCII art to stdout.
            print(ascii_art)

        sys.exit()  # <- EXIT!


    #######################
    # Define and run tests.
    #######################
    import unittest


    class TestColorizeLine(unittest.TestCase):
        def setUp(self):
            self.addCleanup(lambda: sys.stdout.write(Style.RESET_ALL))

        def test_single_color(self):
            result = colorize_line('Hello', 'bbbbb', {'b': Fore.BLUE})
            self.assertEqual(result, '\x1b[34mHello')

        def test_multi_color(self):
            result = colorize_line(
                'HelloWorld',
                'bbbbbyyyyy',
                {'b': Fore.BLUE, 'y': Fore.YELLOW},
            )
            self.assertEqual(result, '\x1b[34mHello\x1b[33mWorld')

        def test_space_characters(self):
            """If unspecified, spaces should get no style."""
            result = colorize_line(
                'Hello World',
                'bbbbb yyyyy',
                {'b': Fore.BLUE, 'y': Fore.YELLOW},
            )
            self.assertEqual(result, '\x1b[34mHello\x1b[0m \x1b[33mWorld')

        def test_different_lengths(self):
            longer_art = 'Hello World'
            shorter_color = 'bbbbb'
            result = colorize_line(longer_art, shorter_color, {'b': Fore.BLUE})
            self.assertEqual(result, '\x1b[34mHello\x1b[0m World')

            shorter_art = 'Hello'
            longer_color = 'yyyyyyyyyyy'
            result = colorize_line(shorter_art, longer_color, {'y': Fore.YELLOW})
            self.assertEqual(result, '\x1b[33mHello      ')


    unittest.main(argv=sys.argv[:1])
