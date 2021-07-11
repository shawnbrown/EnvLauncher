# Copyright (C) 2021 Shawn Brown.
#
# This file is part of EnvLauncher.
#
# EnvLauncher is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EnvLauncher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EnvLauncher.  If not, see <https://www.gnu.org/licenses/>.

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
    import textwrap

    examples = textwrap.dedent("""
        examples:
          Print ASCII banner to stdout:
            python %(prog)s

          Save ASCII banner to file:
            python %(prog)s save output.ascii

          Run test suite:
            python %(prog)s test

          Run test suite with verbose flag:
            python %(prog)s test -v
    """)
    parser = argparse.ArgumentParser(
        epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(
        title='sub-commands', dest='command', help='available sub-commands')

    parser_test = subparsers.add_parser('save', help='Save ASCII art to file.')
    parser_test.add_argument('file', help='filename to save to', metavar='FILE')

    # This subparser mimics unittest's arguments.
    parser_test = subparsers.add_parser('test', help='Run test suite.')
    parser_test.add_argument('-v', '--verbose', action='store_const', const=2,
                             help='Verbose output', dest='verbosity')
    parser_test.add_argument('-q', '--quiet', action='store_const', const=0,
                             help='Quiet output', dest='verbosity')
    parser_test.add_argument('--locals', action='store_true',
                             help='Show local variables in tracebacks',
                             dest='tb_locals')
    parser_test.add_argument('-f', '--failfast', action='store_true',
                             help='Stop on first fail or error', dest='failfast')
    parser_test.add_argument('-c', '--catch', action='store_true',
                             help='Catch Ctrl-C and display results so far')
    parser_test.add_argument('-b', '--buffer', action='store_true',
                             help='Buffer stdout and stderr during tests',
                             dest='buffer')

    args = parser.parse_args()


    ########################
    # Print color ASCII art.
    ########################
    if args.command is None:
        ascii_art = colorize_ascii_art(art_layer, color_layer, color_codes)
        print(ascii_art)
        sys.exit()  # <- EXIT!


    #######################
    # Save color ASCII art.
    #######################
    if args.command == 'save':
        path = pathlib.Path(args.file)
        if path.exists():
            sys.exit(f'Cannot save: {path} already exists')  # <- EXIT!

        ascii_art = colorize_ascii_art(art_layer, color_layer, color_codes)
        with open(path, 'w') as fh:
            fh.write(ascii_art)
        print(f'ASCII art saved to {path}')
        sys.exit()  # <- EXIT!


    #######################
    # Define and run tests.
    #######################
    if args.command != 'test':
        msg = 'All commands other than "test" should be handled already.'
        raise Exception(msg)

    import unittest


    class TestColorizeLine(unittest.TestCase):
        def setUp(self):
            self.addCleanup(lambda: sys.stdout.write(Style.RESET_ALL))

        def test_no_color(self):
            """Should start with a leading reset code."""
            result = colorize_line('Hello', 'xxxxx', {'x': Style.RESET_ALL})
            self.assertEqual(result, '\x1b[0mHello')

        def test_single_color(self):
            """Should start with color code and end with a reset."""
            result = colorize_line('Hello', 'bbbbb', {'b': Fore.BLUE})
            self.assertEqual(result, '\x1b[34mHello\x1b[0m')

        def test_multi_color(self):
            result = colorize_line(
                'HelloWorld',
                'bbbbbyyyyy',
                {'b': Fore.BLUE, 'y': Fore.YELLOW},
            )
            self.assertEqual(result, '\x1b[34mHello\x1b[33mWorld\x1b[0m')

        def test_art_longer_than_color(self):
            """Extra art characters should get no styles (reset code)."""
            art_line = 'Hello World'  # <- 11 characters (6 extra)
            color_line = 'bbbbb'      # <- 5 codes
            result = colorize_line(
                art_line,
                color_line,
                {'b': Fore.BLUE, ' ': Style.RESET_ALL},
            )
            self.assertEqual(result, '\x1b[34mHello\x1b[0m World')

        def test_art_shorter_than_color(self):
            """Extra style codes should be applied to space characters."""
            art_line = 'Hello'          # <- 5 characters
            color_line = 'yyyyyyyyyyy'  # <- 11 codes (6 extra)
            result = colorize_line(
                art_line,
                color_line,
                {'y': Fore.YELLOW},
            )
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
            resets when necessary.

            Without a leading reset (code \x1b[0m), earlier "BRIGHT"
            or "DIM" styles, or earlier background color codes, would
            bleed into later codes that only define forground color.
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
            self.assertEqual(result, '\x1b[0mHello')

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
            expected = '\x1b[0m\x1b[34mHello\x1b[0m \x1b[33mWorld\x1b[0m\n'
            self.assertEqual(result, expected)

        def test_single_leading_newline(self):
            """A leading newline in art and color layers should be removed."""
            result = colorize_ascii_art(
                '\nHello World\n',  # <- starts with newline
                '\nxxxxxxxxxxx\n',  # <- starts with newline
                {'x': Fore.BLUE},
            )
            expected = '\x1b[0m\x1b[34mHello World\x1b[0m\n'  # <- no starting newline
            self.assertEqual(result, expected)

        def test_multiple_leading_newlines(self):
            """If there are multiple leading newlines, only remove one."""
            result = colorize_ascii_art(
                '\n\n\nHello World\n',  # <- starts with 3 newlines
                '\n\n\nxxxxxxxxxxx\n',  # <- starts with 3 newlines
                {'x': Fore.BLUE},
            )
            expected = '\x1b[0m\n\n\x1b[34mHello World\x1b[0m\n'  # <- 2 newlines
            self.assertEqual(result, expected)

        def test_mismatched_line_count(self):
            """Should render all art and colors even if they have a
            different number of lines.
            """
            art_layer = 'Hello\nWorld\n'
            color_layer = 'bbbbb'
            color_codes = {'b': Fore.BLUE}

            result = colorize_ascii_art(art_layer, color_layer, color_codes)
            expected = '\x1b[0m\x1b[34mHello\x1b[0m\n\x1b[0mWorld\n'
            msg = ('The second line of art_layer receives no styles because '
                   'color_layer only contains one row.')
            self.assertEqual(result, expected, msg=msg)


    argv = list(sys.argv)  # Make a copy.
    argv.remove('test')
    unittest.main(argv=argv)  # Pass remaining args to unittest.
