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
import itertools
import os
import re
import subprocess
import tempfile
from typing import List, Tuple


APP_NAME = 'com.github.shawnbrown.EnvLauncher'


class XDGDataPaths(object):
    """Class to fetch data paths that conform to the "XDG Base
    Directory Specification" version 0.8.

    For details see:
        http://standards.freedesktop.org/basedir-spec/
    """
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

    def find_resource_path(self, subdir, filename) -> str:
        """Return file path for the first matching data resource
        found in XDG data locations. If no file is found, raises
        a FileNotFoundError.
        """
        search_dirs = [self.data_home] + self.data_dirs
        resource = os.path.join(subdir, filename)
        for data_dir in search_dirs:
            path = os.path.join(data_dir, resource)
            if os.path.exists(path):
                return os.path.realpath(path)  # <- EXIT!
        raise FileNotFoundError(f'Could not find resource {resource!r}')

    def make_home_path(self, subdir, filename) -> str:
        """Return data home path for given resource."""
        path = os.path.join(self._data_home, subdir, filename)
        return os.path.realpath(path)


class DesktopEntryParser(object):
    """Class to parse .desktop files that conform to the "Desktop Entry
    Specification" version 1.5.

    For details see:
        https://specifications.freedesktop.org/desktop-entry-spec/
    """
    _escape_prefix = '_COMMENT'
    _escape_suffix = 'ZZ=ZZ'
    _escape_regex = re.compile(f'{_escape_prefix}\\d+{_escape_suffix}')
    _venv_prefix = 'venv'
    _identifier_num = itertools.count(1)

    def __init__(self, f):
        string = f.read(128 * 1024)  # Read 128 kB from file.
        if f.read(1):
            raise RuntimeError('Desktop entry file exceeds 128 kB.')

        self._parser = configparser.ConfigParser(
            dict_type=collections.OrderedDict,
            delimiters=('=',),
            allow_no_value=True,
            comment_prefixes=None,
        )
        self._parser.optionxform = str  # Use option names as-is (no case-folding).
        string = self._escape_comments(string)
        self._parser.read_string(string)

        self._rcfile = self._parser.get('X-EnvLauncher Preferences', 'Rcfile', fallback='')
        self._banner = self._parser.get('X-EnvLauncher Preferences', 'Banner', fallback='color')

    @staticmethod
    def lookahead(iterable, sentinal=None):
        """s -> (s0,s1), (s1,s2), ..., (sN,sentinal)

        Adapted from "pairwise()" recipe in itertools docs.
        """
        a, b = itertools.tee(iterable)
        next(b, None)
        return itertools.zip_longest(a, b, fillvalue=sentinal)

    @classmethod
    def _escape_comments(cls, string) -> str:
        """Escape comment lines so that ConfigParser will retain them."""
        escaped = []
        for index, pair in enumerate(cls.lookahead(string.split('\n')), 1):
            line, nextline = pair
            if (line.startswith('#')                         # <- comment
                    or (line == ''                           # <- blank line
                        and nextline is not None             # <- next not last
                        and not nextline.startswith('['))):  # <- next not section
                line = f'{cls._escape_prefix}{index}{cls._escape_suffix}{line}'
            escaped.append(line)
        return '\n'.join(escaped)

    @classmethod
    def _unescape_comments(cls, string) -> str:
        """Unescape lines to recover original comments."""
        escaped = []
        for line in string.split('\n'):
            if cls._escape_regex.match(line):
                _, _, line = line.partition(cls._escape_suffix)
            escaped.append(line)
        return '\n'.join(escaped)

    @classmethod
    def from_string(cls, string):
        return cls(io.StringIO(string))

    def export_string(self) -> str:
        f = io.StringIO()
        self._parser.write(f, space_around_delimiters=False)
        string = self._unescape_comments(f.getvalue())
        return f'{string.strip()}\n'

    @property
    def rcfile(self) -> str:
        """An "rc" file to execute after activating the environment
        (e.g., ~/.bashrc).
        """
        return self._rcfile

    @rcfile.setter
    def rcfile(self, value):
        if not isinstance(value, str):
            value = ''
        self._rcfile = value

    @property
    def banner(self) -> str:
        """Python logo banner option."""
        return self._banner

    @banner.setter
    def banner(self, value):
        if value not in {'color', 'plain', 'none'}:
            value = 'color'
        self._banner = value

    def make_identifier(self) -> str:
        """Generate and return a new action identifier."""
        actions_value = self._parser['Desktop Entry']['Actions']
        identifiers = {x for x in actions_value.split(';') if x.startswith(self._venv_prefix)}

        candidate = f'{self._venv_prefix}{next(self._identifier_num)}'
        while candidate in identifiers:
            candidate = f'{self._venv_prefix}{next(self._identifier_num)}'
        return candidate

    def get_actions(self) -> List[Tuple[str, str, str, str]]:
        """Return sorted list of virtual environment launcher actions."""
        regex = re.compile(r'^envlauncher --activate "(.+)" --directory "(.+)"$')
        action_data = {}
        for section in self._parser.sections():
            if not section.startswith(f'Desktop Action {self._venv_prefix}'):
                continue
            _, _, identifier = section.partition('Desktop Action ')
            name = self._parser[section]['Name']
            match = regex.match(self._parser[section]['Exec'])
            if match:
                activate, directory = match.group(1, 2)
                action_data[identifier] = (identifier, name, activate, directory)

        identifiers = self._parser.get('Desktop Entry', 'Actions', fallback='')
        identifiers = [x.strip() for x in identifiers.rstrip(';').split(';')]

        # Get action data in identifier order.
        actions = []
        for ident in identifiers:
            action = action_data.pop(ident, None)
            if action:
                actions.append(action)
        return actions

    def set_actions(self, actions: List[Tuple[str, str, str, str]]):
        """Set virtual environment launcher actions."""
        # Remove existing venv action groups.
        for section in self._parser.sections():
            if section.startswith(f'Desktop Action {self._venv_prefix}'):
                del self._parser[section]

        # Add venv action groups and collect identifiers.
        venv_identifiers = []
        for identifier, name, activate, directory in actions:
            self._parser[f'Desktop Action {identifier}'] = {
                'Name': name.strip(),
                'Exec': f'envlauncher --activate "{activate}" --directory "{directory}"',
            }
            venv_identifiers.append(identifier)

        # Get current identifiers and remove old venv identifiers.
        actions_value = self._parser['Desktop Entry']['Actions']
        other_identifiers = actions_value.rstrip(';').split(';')
        other_identifiers = [x for x in other_identifiers if not x.startswith(self._venv_prefix)]

        # Update the Desktop Entry group's Actions value.
        actions_value = ';'.join(venv_identifiers + other_identifiers)
        self._parser['Desktop Entry']['Actions'] = f'{actions_value};'


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


def edit_preferences(reset_all=False, environ=None):
    """Edit preferences."""
    paths = XDGDataPaths(os.environ if environ is None else environ)

    # Temporarily use shutil.copy() to prevent users from directly
    # opening a file they don't have write permissions for (e.g.
    # a file in "/usr/local/share/applications/...").
    import shutil
    desktop_home = paths.make_home_path('applications', f'{APP_NAME}.desktop')
    if not os.path.exists(desktop_home):
        desktop_path = paths.find_resource_path('applications', f'{APP_NAME}.desktop')
        shutil.copy(src=desktop_path, dst=desktop_home)

    # Temporarily open file in Gedit until GUI is ready.
    args = ['gedit', '--standalone', '--class', APP_NAME, desktop_home]
    process = subprocess.Popen(args)


def main():
    args = parse_args()
    if args.activate:
        activate_environment(args.activate, args.directory)
    elif args.preferences:
        edit_preferences(args.reset_all)


if __name__ == '__main__':
    main()
