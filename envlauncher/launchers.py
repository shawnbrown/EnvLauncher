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
import re
import shlex
import subprocess
import sys
import warnings
from time import sleep, time
from typing import List, Optional


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


class AlacrittyLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = [
            '--class', f'{self.app_id},{self.app_id}',
            '--title', 'EnvLauncher',
            '-e', 'bash', '--rcfile', script_path
        ]

    @property
    def command(self) -> str:
        return 'alacritty'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


class CoolRetroTermLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = ['-e', 'bash', '--rcfile', script_path]

    @property
    def command(self) -> str:
        return 'cool-retro-term'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


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


class GuakeLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = [
            '--no-startup-script',
            '--new-tab', '.',
            '--show',
            '-e', f'clear;source {shlex.quote(script_path)}',
        ]

    @property
    def command(self) -> str:
        return 'guake'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


class KittyLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = [
            '--class', self.app_id,
            'bash', '--rcfile', script_path
        ]

    @property
    def command(self) -> str:
        return 'kitty'

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


class QTerminalLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = [
            '--name', self.app_id,
            '-e', f'bash --rcfile {shlex.quote(script_path)}',
        ]

    @property
    def command(self) -> str:
        return 'qterminal'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


class SakuraLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = [
            '--class', self.app_id,
            '--icon', self.app_id,
            '-e', 'bash', '--rcfile', script_path,
        ]

    @property
    def command(self) -> str:
        return 'sakura'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


class TerminatorLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.args = [
            '--name', self.app_id,
            '--icon', self.app_id,
            '--no-dbus',  # <- For clean grouping in dash/taskbar.
            '-x', 'bash', '--rcfile', script_path
        ]

    @property
    def command(self) -> str:
        return 'terminator'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


class Xfce4Terminal(BaseLauncher):
    """The default terminal emulator for the Xfce Desktop."""
    def __init__(self, script_path):
        self.args = [
            '--startup-id', self.app_id,
            '--icon', self.app_id,
            '--initial-title', 'EnvLauncher',
            '-x', 'bash', '--rcfile', script_path,
        ]

    @property
    def command(self) -> str:
        return 'xfce4-terminal'

    def __call__(self) -> subprocess.Popen:
        return subprocess.Popen([self.command] + self.args)


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


class YakuakeLauncher(BaseLauncher):
    def __init__(self, script_path):
        self.script_path = script_path

    @property
    def command(self) -> str:
        return 'yakuake'

    @staticmethod
    def build_args(object_path, method, *contents) -> List[str]:
        """Return a list of arguments for using the `dbus-send`
        command to call methods of the Yakuake D-Bus connection
        (org.kde.yakuake).

        If *method* is a fully qualified name ("interface.member"),
        it will be used as-is. But if it's unqualified, then
        "org.kde.yakuake" will be used as the member's default
        interface.
        """
        args = [
            'dbus-send',
            '--session',
            '--dest=org.kde.yakuake',
            '--print-reply=literal',
            '--type=method_call',
            object_path,
            method if ('.' in method) else f'org.kde.yakuake.{method}',
        ]
        return args + list(contents)

    @staticmethod
    def parse_session_id(reply: bytes) -> int:
        """Takes an `addSession` reply and returns the id as an int."""
        reply = str(reply, encoding=sys.stdout.encoding)
        matched = re.search(r'(?:int16|int32|int64)[ ](\d+)', reply)
        if not matched:
            msg = f'Unable to get Yakuake tab session-id: {reply!r}'
            raise RuntimeError(msg)
        return int(matched.group(1))

    @classmethod
    def is_visible(cls):
        """Check if the Yakuake console is currently visible."""
        args = cls.build_args(
            '/yakuake/MainWindow_1',
            'org.freedesktop.DBus.Properties.Get',
            'string:org.qtproject.Qt.QWidget',
            'string:visible',
        )
        try:
            reply = subprocess.check_output(args, stderr=subprocess.PIPE, timeout=5)
        except subprocess.CalledProcessError as e:
            if e.stderr:
                print(e.stderr, file=sys.stderr)
                if b"No such object path '/yakuake/MainWindow_1'" in e.stderr:
                    return False  # If MainWindow_1 path not available, assume false.
            raise
        return b'boolean true' in reply

    @classmethod
    def toggle_window(cls):
        """Toggle console from open-to-closed or closed-to-open."""
        args = cls.build_args('/yakuake/window', 'toggleWindowState')
        subprocess.run(args, timeout=5, check=True)

    def __call__(self):
        # Create a new tab and get its session-id.
        args = self.build_args('/yakuake/sessions', 'addSession')
        reply = subprocess.check_output(args, timeout=5)
        yakuake_session = self.parse_session_id(reply)

        # Start the virtual environment in the new tab.
        args = self.build_args(
            '/yakuake/sessions',
            'runCommandInTerminal',
            f'int32:{yakuake_session}',
            f'string:clear;source {shlex.quote(self.script_path)}',
        )
        subprocess.run(args, timeout=5, check=True)

        # Set the new tab's name.
        args = self.build_args(
            '/yakuake/tabs',
            'setTabTitle',
            f'int32:{yakuake_session}',
            'string:EnvLauncher',
        )
        subprocess.run(args, timeout=5, check=True)

        # Open the console.
        if not self.is_visible():
            self.toggle_window()
        return os.EX_OK
