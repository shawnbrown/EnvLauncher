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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--activate',
        help='environment activation script',
        metavar='SCRIPT',
    )
    parser.add_argument(
        '--directory',
        help=f'working directory path (default ~)',
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
    return args


def launch_environment():
    """Launch a gnome-terminal and activate a development environment."""
    parser = argparse.ArgumentParser()
    parser.add_argument('script', help='Path to the environment activation script.')
    parser.add_argument('--dir', help='Working directory.')
    args = parser.parse_args()

    rcfile_lines = [
        f'source {args.script}',
        f'cd {args.dir}' if args.dir else '',
    ]

    with tempfile.NamedTemporaryFile(mode='w+') as fh:
        fh.write('\n'.join(rcfile_lines))
        fh.seek(0)

        args = ['gnome-terminal', '--', 'bash', '--rcfile', fh.name]
        process = subprocess.Popen(args)
        process.wait(10)


if __name__ == '__main__':
    launch_environment()
