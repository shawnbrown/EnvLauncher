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

"""Application logic for EnvLauncher."""

import collections
import configparser
import io
import itertools
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from time import sleep, time
from typing import List, Tuple, Optional

from . import launchers


APP_NAME = 'com.github.shawnbrown.EnvLauncher'
__version__ = '0.1a1.dev1'


class DataPaths(object):
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


def get_terminal_emulators() -> List[str]:
    """Return a list of supported terminal emulators available
    on the system.
    """
    supported = [
        'gnome-terminal',  # GNOME default
        'terminator',
        'konsole',  # KDE default
        'guake',
        'yakuake',
        'alacritty',
        'kitty',
        'xfce4-terminal',  # XFCE default
        'qterminal',  # LXQt default
        'xterm',
        'sakura',
        'cool-retro-term',
    ]

    available = []
    for terminal_emulator in supported:
        if shutil.which(terminal_emulator):
            available.append(terminal_emulator)

    if not available:
        import warnings
        warnings.warn('No supported terminal emulators available.')
    return available


class Settings(object):
    """Class to manage settings for EnvLauncher application.

    Settings are loaded from and saved to the desktop entry file used
    to launch the application (the ".desktop" file). This file should
    conform to the "Desktop Entry Specification" version 1.5.

    For details see:

        https://specifications.freedesktop.org/desktop-entry-spec/
    """
    _escape_prefix = '_COMMENT'
    _escape_suffix = 'ZZ=ZZ'
    _escape_regex = re.compile(f'{_escape_prefix}\\d+{_escape_suffix}')
    _venv_prefix = 'venv'

    def __init__(self, file_or_path):
        """Read desktop entry file and load it into a ConfigParser."""
        if isinstance(file_or_path, str):
            f = open(file_or_path)  # If not already open, open file locally.
        else:
            f = file_or_path

        try:
            string = f.read(128 * 1024)  # Read 128 kB from file.
            if f.read(1):
                raise RuntimeError('Desktop entry file exceeds 128 kB.')
                # If a desktop entry file is anywhere near 128 kB,
                # then something unexpected is going on.
        finally:
            if f != file_or_path:  # If opened locally, then close it.
                f.close()

        self._parser = configparser.ConfigParser(
            dict_type=collections.OrderedDict,
            delimiters=('=',),
            allow_no_value=True,
            comment_prefixes=None,
        )
        self._parser.optionxform = str  # Use option names as-is (no case-folding).
        string = self._escape_comments(string)
        self._parser.read_string(string)

        self._terminal_emulator_choices = get_terminal_emulators()
        self._rcfile = self._parser.get('X-EnvLauncher Options', 'Rcfile', fallback='')
        self._banner = self._parser.get('X-EnvLauncher Options', 'Banner', fallback='color')
        self._venv_number = itertools.count(1)
        self._app_data_subdir = 'envlauncher'

    @staticmethod
    def _lookahead(iterable, sentinal=None):
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
        for index, pair in enumerate(cls._lookahead(string.split('\n')), 1):
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
    def terminal_emulator_choices(self) -> List[str]:
        return self._terminal_emulator_choices

    @property
    def terminal_emulator(self) -> Optional[str]:
        """Terminal emulator to use when activating environment."""
        value = self._parser.get(section='X-EnvLauncher Options',
                                 option='TerminalEmulator', fallback=None)
        if value in self.terminal_emulator_choices:
            return value
        if self.terminal_emulator_choices:
            return self.terminal_emulator_choices[0]
        return None

    @terminal_emulator.setter
    def terminal_emulator(self, value):
        self._parser['X-EnvLauncher Options']['TerminalEmulator'] = value

    @property
    def banner(self) -> str:
        """Python logo banner option."""
        return self._banner

    @banner.setter
    def banner(self, value):
        if value not in {'color', 'plain', 'none'}:
            value = 'color'
        self._banner = value

    @property
    def banner_resource(self) -> Optional[Tuple[str, str]]:
        """A two-tuple containing the subdirectory and filename of the
        banner file (if defined).
        """
        if self.banner == 'color':
            filename = 'banner-color.ascii'
        elif self.banner == 'plain':
            filename = 'banner-plain.ascii'
        else:
            return None
        return (self._app_data_subdir, filename)

    def make_identifier(self) -> str:
        """Generate and return a new action identifier."""
        actions_value = self._parser['Desktop Entry']['Actions']
        identifiers = {x for x in actions_value.split(';') if x.startswith(self._venv_prefix)}

        candidate = f'{self._venv_prefix}{next(self._venv_number)}'
        while candidate in identifiers:
            candidate = f'{self._venv_prefix}{next(self._venv_number)}'
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

        actions_value = self._parser.get('Desktop Entry', 'Actions', fallback='')
        identifiers = [x.strip() for x in actions_value.rstrip(';').split(';')]

        # Get action data in identifier order.
        actions = []
        for ident in identifiers:
            action = action_data.pop(ident, None)
            if action:
                actions.append(action)
        return actions

    def set_actions(self, actions: List[Tuple[str, str, str, str]]):
        """Set virtual environment launcher actions.

        This replaces all of the existing launcher actions with the
        given list.
        """
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
        actions_value = self._parser.get('Desktop Entry', 'Actions', fallback='')
        identifiers = actions_value.rstrip(';').split(';')
        func = lambda x: x and not x.startswith(self._venv_prefix)
        other_identifiers = [x for x in identifiers if func(x)]

        # Update the Desktop Entry group's Actions value.
        actions_value = ';'.join(venv_identifiers + other_identifiers)
        self._parser['Desktop Entry']['Actions'] = f'{actions_value};'


class EnvLauncherApp(object):
    """A class to prepare and launch virtual environment sessions."""
    def __init__(self):
        self.paths = DataPaths()
        desktop_path = self.paths.find_resource_path('applications', f'{APP_NAME}.desktop')
        self.settings = Settings(desktop_path)

    def _build_rcfile(self, environment, working_dir, file_to_delete) -> str:
        """Build and return rcfile text to use when launching bash."""
        rcfile_lines = []

        # First, change directory so relative paths reference new location.
        rcfile_lines.append(f'cd {working_dir}')

        # Execute user rcfile (~/.bashrc or other).
        if self.settings.rcfile:
            rcfile_lines.append(f'source {self.settings.rcfile}')

        # Add line to activate the environment!
        rcfile_lines.append(f'source {environment}')

        # Display the ASCII banner.
        if self.settings.banner_resource:
            subdir, filename = self.settings.banner_resource
            banner_path = self.paths.find_resource_path(subdir, filename)
            rcfile_lines.append(f'cat {banner_path}')

        # The *file_to_delete* should be the name of the rcfile itself.
        # This way, it will remove itself when executed and we won't
        # need to wait before cleaning it up later.
        rcfile_lines.append(f'rm {shlex.quote(file_to_delete)}')

        # Blank entry to assure trailing "\n".
        rcfile_lines.append('')

        return '\n'.join(rcfile_lines)

    def get_launcher(self, terminal_emulator, rcfile_name):
        """Returns a function and arguments used to launch a terminal
        emulator and activate a virtual environment.
        """
        if terminal_emulator == 'gnome-terminal':
            return launchers.GnomeTerminalLauncher(rcfile_name)

        if terminal_emulator == 'terminator':
            args = ['terminator',
                    '--name', APP_NAME,
                    '--icon', APP_NAME,
                    '--no-dbus',  # <- For clean grouping in dash/taskbar.
                    '-x', 'bash', '--rcfile', rcfile_name]
            return lambda: subprocess.Popen(args)

        if terminal_emulator == 'xterm':
            return launchers.XTermLauncher(rcfile_name)

        if terminal_emulator == 'konsole':
            return launchers.KonsoleLauncher(rcfile_name)

        if terminal_emulator == 'alacritty':
            args = ['alacritty',
                    '--class', f'{APP_NAME},{APP_NAME}',
                    '--title', 'EnvLauncher',
                    '-e', 'bash', '--rcfile', rcfile_name]
            return lambda: subprocess.Popen(args)

        if terminal_emulator == 'kitty':
            args = ['kitty',
                    '--class', APP_NAME,
                    'bash', '--rcfile', rcfile_name]
            return lambda: subprocess.Popen(args)

        if terminal_emulator == 'guake':
            args = ['guake',
                    '--no-startup-script',
                    '--new-tab', '.',
                    '--show',
                    '-e', f'clear;source {shlex.quote(rcfile_name)}']
            return lambda: subprocess.Popen(args)

        if terminal_emulator == 'yakuake':
            return launchers.YakuakeLauncher(rcfile_name)

        # XFCE default terminal.
        if terminal_emulator == 'xfce4-terminal':
            args = ['xfce4-terminal',
                    '--startup-id', APP_NAME,
                    '--icon', APP_NAME,
                    '--initial-title', 'EnvLauncher',
                    '-x', 'bash', '--rcfile', rcfile_name]
            return lambda: subprocess.Popen(args)

        # LXQt default terminal.
        if terminal_emulator == 'qterminal':
            args = ['qterminal',
                    '--name', APP_NAME,
                    '-e', f'bash --rcfile {shlex.quote(rcfile_name)}']
            return lambda: subprocess.Popen(args)

        if terminal_emulator == 'sakura':
            args = ['sakura',
                    '--class', APP_NAME,
                    '--icon', APP_NAME,
                    '-e', 'bash', '--rcfile', rcfile_name]
            return lambda: subprocess.Popen(args)

        if terminal_emulator == 'cool-retro-term':
            args = ['cool-retro-term', '-e', 'bash', '--rcfile', rcfile_name]
            return lambda: subprocess.Popen(args)

        raise Exception(f'Unsupported terminal emulator {terminal_emulator!r}')

    def __call__(self, environment, working_dir=None):
        """Launch a terminal emulator and activate a dev environment."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as rcfile:
                rcfile_text = self._build_rcfile(environment,
                                                 working_dir,
                                                 file_to_delete=rcfile.name)
                rcfile.write(rcfile_text)

            func = self.get_launcher(
                terminal_emulator=self.settings.terminal_emulator,
                rcfile_name=rcfile.name,
            )
            func()

        except Exception:
            try:
                os.remove(rcfile.name)
            except FileNotFoundError:
                pass
            raise


def configure_envlauncher(paths, reset_all=False):
    """Configure EnvLauncher settings."""
    # Temporarily use shutil.copy() to prevent users from directly
    # opening a file they don't have write permissions for (e.g.
    # a file in "/usr/local/share/applications/...").
    desktop_home = paths.make_home_path('applications', f'{APP_NAME}.desktop')
    if not os.path.exists(desktop_home):
        desktop_path = paths.find_resource_path('applications', f'{APP_NAME}.desktop')
        os.makedirs(os.path.dirname(desktop_home), exist_ok=True)
        shutil.copy(src=desktop_path, dst=desktop_home)

    # Open file in text editor (will be replaced with GUI).
    if shutil.which('gedit'):
        args = ['gedit', '--standalone', '--class', APP_NAME, desktop_home]
    elif shutil.which('kate'):
        args = ['kate', '--new', '--desktopfile', APP_NAME, desktop_home]
    elif shutil.which('featherpad'):
        args = ['featherpad', '--standalone', desktop_home]
    process = subprocess.Popen(args)
