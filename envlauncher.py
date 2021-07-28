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
import collections
import configparser
import io
import os
import subprocess
import tempfile
from typing import List


class XDGDirectory(object):
    def __init__(self, environ=None):
        environ = dict(os.environ if environ is None else environ)

        self._data_home = (environ.get('XDG_DATA_HOME')
                           or os.path.join(environ.get('HOME'), '.local', 'share'))
        self._data_dirs = (environ.get('XDG_DATA_DIRS')
                           or '/usr/local/share:/usr/share').split(':')

    @property
    def data_home(self) -> str:
        """The base directory for user-specific data files."""
        return self._data_home

    @property
    def data_dirs(self) -> List[str]:
        """Directories to search for data files in order of preference."""
        return self._data_dirs

    def find_first_filepath(self, subdir, filename) -> str:
        """Return first matching resource from XDG data locations."""
        search_dirs = [self.data_home] + self.data_dirs
        resource = os.path.join(subdir, filename)
        for data_dir in search_dirs:
            path = os.path.join(data_dir, resource)
            if os.path.exists(path):
                return os.path.realpath(path)  # <- EXIT!
        raise FileNotFoundError(f'Could not find resource {resource!r}')

    def make_home_filepath(self, subdir, filename) -> str:
        path = os.path.join(self._data_home, subdir, filename)
        return os.path.realpath(path)


class XDGDesktop(object):
    def __init__(self):
        self.config = configparser.ConfigParser(
            dict_type=collections.OrderedDict,
            delimiters=('=',),
            allow_no_value=True,
            comment_prefixes=None,
        )
        self.config.optionxform = str  # Use option names as-is (no case-folding).

    def read_string(self, string):
        self.config.read_string(string)

    def export_string(self):
        fh = io.StringIO()
        self.config.write(fh, space_around_delimiters=False)
        return fh.getvalue()


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


def activate_environment(script_path, working_dir):
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


def edit_preferences(reset_all=False):
    """Edit preferences."""
    raise NotImplementedError


def main():
    args = parse_args()
    if args.activate:
        activate_environment(args.activate, args.directory)
    elif args.preferences:
        edit_preferences(args.reset_all)


if __name__ == '__main__':
    main()
