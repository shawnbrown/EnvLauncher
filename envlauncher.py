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

import argparse
import subprocess
import tempfile


def parse_args(args=None):
    """Parse command line arguments."""
    usage = (
        '\n'
        '  %(prog)s [-h]\n'
        '  %(prog)s --activate SCRIPT [--directory PATH]\n'
        '  %(prog)s --preferences [--reset-all]'
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
        '--preferences',
        action='store_true',
        help='show preferences window',
    )
    parser.add_argument(
        '--reset-all',
        action='store_true',
        help='reset all preferences',
    )

    args = parser.parse_args(args=args)

    # Check that arguments conform to `usage` examples.
    if args.activate and args.preferences:
        parser.error('argument --activate cannot be used with --preferences')
    if args.directory and not args.activate:
        parser.error('argument --activate is required when using --directory')
    if args.reset_all and not args.preferences:
        parser.error('argument --preferences is required when using --reset-all')

    return args


def launch_environment(script_path, working_dir):
    """Launch a gnome-terminal and activate a development environment."""
    rcfile_lines = [
        f'source {script_path}',
        f'cd {working_dir}' if working_dir else '',
    ]

    with tempfile.NamedTemporaryFile(mode='w+') as fh:
        fh.write('\n'.join(rcfile_lines))
        fh.seek(0)

        args = ['gnome-terminal', '--', 'bash', '--rcfile', fh.name]
        process = subprocess.Popen(args)
        process.wait(10)


def main():
    args = parse_args()
    if args.activate:
        launch_environment(args.activate, args.directory)
    elif args.preferences:
        pass


if __name__ == '__main__':
    main()
