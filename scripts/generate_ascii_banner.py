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

    zipped = itertools.zip_longest(art_line, color_line, fillvalue=' ')
    for character, code in zipped:
        if prev_code != code:
            rendered_characters.append(color_codes[code])
            prev_code = code
        rendered_characters.append(character)

    colored_line = ''.join(rendered_characters)
    if colored_line and color_codes[prev_code] != Style.RESET_ALL:
        colored_line = f'{colored_line}{Style.RESET_ALL}'
    return colored_line


def colorize_ascii_art(art_layer, color_layer, color_codes):
    if art_layer.startswith('\n') and color_layer.startswith('\n'):
        art_layer = art_layer[1:]
        color_layer = color_layer[1:]

    art_lines = art_layer.split('\n')
    color_lines = color_layer.split('\n')
    color_codes = dict(color_codes)  # Make a copy.
    if ' ' not in color_codes:
        color_codes[' '] = Style.RESET_ALL

    codes_used = set(color_layer)
    codes_used.discard('\n')
    undefined_codes = codes_used - set(color_codes.keys())
    if undefined_codes:
        msg = (
            f'color_layer contains codes not defined in color_codes: '
            f'{", ".join(sorted(undefined_codes))}'
        )
        raise ValueError(msg)

    rendered_lines = []
    zipped = itertools.zip_longest(art_lines, color_lines, fillvalue='')
    for art_line, color_line in zipped:
        line = colorize_line(art_line, color_line, color_codes)
        rendered_lines.append(line)

    ascii_art = '\n'.join(rendered_lines)
    if not ascii_art.startswith(Style.RESET_ALL):
        ascii_art = f'{Style.RESET_ALL}{ascii_art}'
    return ascii_art


art_layer = """
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

color_layer = """
           BBBBB                                     g
         BBBBBBBBBB                               g  g
        B  BBBBBBBB                gggggg g    g ggg gggggg gggggg gggggg
        BBBBBBBBBBB                g    g g    g  g  g    g g    g gg  gg
      BBBBBBBBBBBBB                g    g g    g  g  g    g g    g g    g
 BBBBBBBBBBBBBBBBBB YYYYYYY        gggggg gggggg  gg g    g gggggg g    g
BBBBBBBBBBBBBBBBBBB YYYYYYYY       g           g
BBBBBBBBBBBBBBBBBB YYYYYYYYY       g         ggg                             b
BBBBBBBBB YYYYYYYYYYYYYYYYYY                                                 b
BBBBBBBB YYYYYYYYYYYYYYYYYYY bbbbbb bbbbbb b   b   b bbbbbb bbbbbbbbbbb bbbbbb
 BBBBBBB YYYYYYYYYYYYYYYYYY  b    b b    b bb bbb bb bbbbbb b    bbbbbb b    b
         YYYYYYYYYYYYY       b    b b    b bbbbbbbbb bb     b    bb     b    b
         YYYYYYYYYYY         bbbbbb bbbbbb  bbb bbb  bbbbbb b    bbbbbb bbbbbb
         YYYYYYYY  Y         b
         YYYYYYYYYY          b
            YYYYY
"""

color_codes = {
    'B': Style.BRIGHT + Fore.BLUE,
    'Y': Style.BRIGHT + Fore.YELLOW,
    'g': Style.DIM + Fore.WHITE,
    'b': Fore.BLUE,
}


if __name__ == '__main__':
    import argparse
    import pathlib
    import sys


    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--test', action='store_true', help='Run test suite.')
    group.add_argument('--save', metavar='FILE', help='Save ASCII art to file.')

    args = parser.parse_args()


    ################################
    # Save or print color ASCII art.
    ################################
    if args.test == False:
        # Generate color ASCII art.
        ascii_art = colorize_ascii_art(art_layer, color_layer, color_codes)

        # Save ASCII art to a text file.
        if args.save:
            path = pathlib.Path(args.save)
            if path.exists():
                sys.exit(f'Cannot save: {path} already exists')  # <- EXIT!

            with open(path, 'w') as fh:
                fh.write(ascii_art)
            print(f'ASCII art saved to {path}')

        # Print the ASCII art to stdout.
        else:
            print(ascii_art)

        sys.exit()  # <- EXIT!


    #######################
    # Define and run tests.
    #######################
    import unittest


    class TestColorizeLine(unittest.TestCase):
        def setUp(self):
            self.addCleanup(lambda: sys.stdout.write(Style.RESET_ALL))

        def test_no_color(self):
            result = colorize_line('Hello', 'xxxxx', {'x': Style.RESET_ALL})
            self.assertEqual(result, '\x1b[0mHello')

        def test_single_color(self):
            """Should start with color code and end with reset."""
            result = colorize_line('Hello', 'bbbbb', {'b': Fore.BLUE})
            self.assertEqual(result, '\x1b[34mHello\x1b[0m')

        def test_multi_color(self):
            result = colorize_line(
                'HelloWorld',
                'bbbbbyyyyy',
                {'b': Fore.BLUE, 'y': Fore.YELLOW},
            )
            self.assertEqual(result, '\x1b[34mHello\x1b[33mWorld\x1b[0m')

        def test_different_lengths(self):
            longer_art = 'Hello World'
            shorter_color = 'bbbbb'
            result = colorize_line(
                longer_art,
                shorter_color,
                {'b': Fore.BLUE, ' ': Style.RESET_ALL},
            )
            self.assertEqual(result, '\x1b[34mHello\x1b[0m World')

            shorter_art = 'Hello'
            longer_color = 'yyyyyyyyyyy'
            result = colorize_line(shorter_art, longer_color, {'y': Fore.YELLOW})
            self.assertEqual(result, '\x1b[33mHello      \x1b[0m')


    class TestColorizeAsciiArt(unittest.TestCase):
        def setUp(self):
            self.addCleanup(lambda: sys.stdout.write(Style.RESET_ALL))

        def test_undefined_color_codes(self):
            regex = \
                'color_layer contains codes not defined in color_codes: x, y'

            with self.assertRaisesRegex(ValueError, regex):
                result = colorize_ascii_art(
                    art_layer='Hello',
                    color_layer='bbbyx',  # <- x and y are undefined in color_codes
                    color_codes={'b': Fore.BLUE, 'r': Fore.RED},
                )

        def test_style_isolation(self):
            r"""Styles should be isolated with leading and trailing
            resets when necessary (escape code \x1b[0m).
            """
            result = colorize_ascii_art('Hello', 'bbbbb', {'b': Fore.BLUE})
            self.assertEqual(result, '\x1b[0m\x1b[34mHello\x1b[0m')

        def test_no_isolation_needed(self):
            """Style-reset codes should only be added where needed."""
            result = colorize_ascii_art('Hello', 'xxxxx', {'x': Style.RESET_ALL})
            msg = (
                'Since the style is explicitly reset, there is no need'
                'for additional style-reset codes.'
            )
            self.assertEqual(result, '\x1b[0mHello', msg=msg)

        def test_colorize(self):
            art_layer = 'Hello World\nHello World\n'
            color_layer = 'bbbbb yyyyy\nyyyyy bbbbb\n'
            color_codes = {'b': Fore.BLUE, 'y': Fore.YELLOW, ' ': Style.RESET_ALL}

            result = colorize_ascii_art(art_layer, color_layer, color_codes)
            expected = (
                '\x1b[0m\x1b[34mHello\x1b[0m \x1b[33mWorld\x1b[0m\n'
                '\x1b[33mHello\x1b[0m \x1b[34mWorld\x1b[0m\n'
            )
            self.assertEqual(result, expected)

        def test_space_characters(self):
            """If unspecified, spaces should get no style."""
            result = colorize_ascii_art(
                'Hello World\n',
                'bbbbb yyyyy\n',
                {'b': Fore.BLUE, 'y': Fore.YELLOW},
            )
            self.assertEqual(result, '\x1b[0m\x1b[34mHello\x1b[0m \x1b[33mWorld\x1b[0m\n')

        def test_single_leading_newline(self):
            """A leading newline in art and color layers should be removed."""
            result = colorize_ascii_art(
                '\nHello World\n',
                '\nxxxxxxxxxxx\n',
                {'x': Fore.BLUE},
            )
            self.assertEqual(result, '\x1b[0m\x1b[34mHello World\x1b[0m\n')

        def test_multiple_leading_newlines(self):
            """If there are multiple leading newlines, only remove one."""
            result = colorize_ascii_art(
                '\n\n\nHello World\n',
                '\n\n\nxxxxxxxxxxx\n',
                {'x': Fore.BLUE},
            )
            self.assertEqual(result, '\x1b[0m\n\n\x1b[34mHello World\x1b[0m\n')

        def test_mismatched_line_count(self):
            """Should render all art and colors even if lengths are not
            the same.
            """
            art_layer = 'Hello\nWorld\n'
            color_layer = 'bbbbb'
            color_codes = {'b': Fore.BLUE}

            result = colorize_ascii_art(art_layer, color_layer, color_codes)
            expected = '\x1b[0m\x1b[34mHello\x1b[0m\n\x1b[0mWorld\n'
            self.assertEqual(result, expected)


    unittest.main(argv=sys.argv[:1])
