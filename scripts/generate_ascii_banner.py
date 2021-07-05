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


    unittest.main(argv=sys.argv[:1])
