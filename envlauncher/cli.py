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

"""Command-line interface for EnvLauncher."""

import argparse
from .app import DataPaths
from .app import EnvLauncherApp
from .app import edit_settings


def parse_args(args=None):
    """Parse command line arguments."""
    usage = (
        '\n'
        '  %(prog)s [-h]\n'
        '  %(prog)s --activate SCRIPT [--directory PATH]\n'
        '  %(prog)s --settings [--reset-all]\n'
        '  %(prog)s --version'
    )
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument(
        '--activate',
        help='environment activation script',
        metavar='SCRIPT',
    )
    parser.add_argument(
        '--directory',
        help='working directory path',
        metavar='PATH',
    )
    parser.add_argument(
        '--settings',
        action='store_true',
        help='open settings manager',
    )
    parser.add_argument(
        '--reset-all',
        action='store_true',
        help='reset all settings',
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='display EnvLauncher version and exit',
    )
    args = parser.parse_args(args=args)

    # Check that arguments conform to `usage` examples.
    if args.activate and args.settings:
        parser.error('argument --activate cannot be used with --settings')
    if args.directory and not args.activate:
        parser.error('argument --activate is required when using --directory')
    if args.reset_all and not args.settings:
        parser.error('argument --settings is required when using --reset-all')
    if args.version and (args.activate or args.settings):
        parser.error('argument --version cannot be used with other arguments')

    return args


def main():
    args = parse_args()
    if args.activate:
        launcher = EnvLauncherApp()
        launcher(args.activate, args.directory)
    elif args.settings:
        paths = DataPaths()
        edit_settings(paths, args.reset_all)
    elif args.version:
        print(__version__)
