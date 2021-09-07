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

"""Terminal emulator launcher classes for EnvLauncher."""

import abc
import os
import subprocess
import warnings
from time import sleep, time
from typing import Optional


class BaseLauncher(abc.ABC):
    """Base class for terminal emulator launchers."""
    app_id = 'com.github.shawnbrown.EnvLauncher'

    @abc.abstractmethod
    def __init__(self, script_path):
        """Initialize launcher (prepare to execute *script_path*)."""

    @property
    @abc.abstractmethod
    def command(self) -> str:
        """Name of terminal emulator command."""
        return '<unspecified>'

    @abc.abstractmethod
    def __call__(self) -> Optional[subprocess.Popen]:
        """Start terminal emulator and run activation script."""
        raise NotImplementedError


class GnomeTerminalLauncher(BaseLauncher):
    """gnome-terminal is the default terminal emulator in the GNOME
    desktop environment.
    """
    def __init__(self, script_path):
        self.args = [
            '--app-id', self.app_id,
            '--', 'bash', '--rcfile', script_path,
        ]

    @property
    def command(self) -> str:
        return 'gnome-terminal'

    @staticmethod
    def _find_gnome_terminal_server() -> Optional[str]:
        """Find and return the path to gnome-terminal-server."""
        search_paths = [
            '/usr/libexec/gnome-terminal-server',
            '/usr/lib/gnome-terminal/gnome-terminal-server',
            '/usr/lib/gnome-terminal-server',
        ]
        for path in search_paths:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def name_has_owner(name) -> bool:
        """Check if the name exists on the session bus (has an owner)."""
        reply = subprocess.check_output([
            'dbus-send',
            '--session',                          # <- use session message bus
            '--dest=org.freedesktop.DBus',        # <- message destination
            '--print-reply=literal',              # <- set reply format
            '--type=method_call',                 # <- message type
            '/',                                  # <- OBJECT_PATH
            'org.freedesktop.DBus.NameHasOwner',  # <- INTERFACE.MEMBER (method)
            f'string:{name}',                     # <- message CONTENTS
        ])
        return b'true' in reply.lower()

    @classmethod
    def _register_app_id(cls, app_id) -> None:
        """Register *app_id* with gnome-terminal-server."""
        if cls.name_has_owner(app_id):
            return  # <- EXIT! (already registered)

        gnome_terminal_server = cls._find_gnome_terminal_server()
        if gnome_terminal_server:
            args = [gnome_terminal_server, '--app-id', app_id]
            if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
                # Class and name determine grouping and icon in KDE.
                args.extend(['--class', app_id, '--name', app_id])
            process = subprocess.Popen(args)
            # Until we can sort-out how to best handle this process,
            # we will filter the ResourceWarning for the specific PID.
            warnings.filterwarnings(
                'ignore',
                message=f'subprocess {process.pid} is still running',
            )

            timeout = time() + 1
            while True:
                sleep(0.03125)  # 1/32nd of a second polling interval
                if cls.name_has_owner(app_id):
                    return  # <- EXIT! (successfully registered)
                if time() > timeout:    # Timeout check must not be used in
                    raise TimeoutError  # the `while` condition--body of loop
        raise OSError                   # MUST execute at least once.

    def __call__(self):
        args = list(self.args)  # Make a copy.
        try:
            # Try to register app-id.
            self._register_app_id(self.app_id)
        except (OSError, TimeoutError):
            # Replace `--app-id` with `--class` (fallback to older behavior).
            args[args.index('--app-id')] = '--class'
        return subprocess.Popen([self.command] + args)


class XTermLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = [
            '-class', self.app_id,
            '-n', self.app_id,  # <- Defines iconName resource.
            '-e', 'bash', '--rcfile', script_path,
        ]

    @property
    def command(self) -> str:
        return 'xterm'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


class KonsoleLauncher(BaseLauncher):
    """Konsole is the default terminal emulator in the KDE
    desktop environment.
    """
    def __init__(self, script_path):
        if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
            args = ['--name', self.app_id]  # Set WM_CLASSNAME in KDE.
        else:
            args = []

        args.extend([
            '-p', f'Icon={self.app_id}',
            '-p', f'LocalTabTitleFormat=EnvLauncher : %D : %n',
            '-e', 'bash', '--rcfile', script_path,
        ])
        self.args = args

    @property
    def command(self) -> str:
        return 'konsole'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)
