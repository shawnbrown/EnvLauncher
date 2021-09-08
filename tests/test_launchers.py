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

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from envlauncher.launchers import BaseLauncher
from envlauncher.launchers import AlacrittyLauncher
from envlauncher.launchers import CoolRetroTermLauncher
from envlauncher.launchers import GnomeTerminalLauncher
from envlauncher.launchers import GuakeLauncher
from envlauncher.launchers import KittyLauncher
from envlauncher.launchers import KonsoleLauncher
from envlauncher.launchers import QTerminalLauncher
from envlauncher.launchers import SakuraLauncher
from envlauncher.launchers import TerminatorLauncher
from envlauncher.launchers import Xfce4Terminal
from envlauncher.launchers import XTermLauncher
from envlauncher.launchers import YakuakeLauncher


class TestAbstractBaseLauncher(unittest.TestCase):
    def test_missing_init(self):
        """Subclasses must define __init__()."""
        class MissingInit(BaseLauncher):
            def __call__(self):
                pass

        with self.assertRaises(TypeError):
            launcher = MissingInit()

    def test_missing_call(self):
        """Subclasses must define __call__()."""
        class MissingCall(BaseLauncher):
            def __init__(self):
                pass

        with self.assertRaises(TypeError):
            launcher = MissingCall()

    def test_missing_command(self):
        """Subclasses must define `command` property."""
        class MissingCommand(BaseLauncher):
            def __init__(self):
                pass

            def __call__(self):
                pass

        with self.assertRaises(TypeError):
            launcher = MissingCommand()

    def test_minimal_subclass(self):
        """Minimal concrete class definition."""
        class MinimalLauncher(BaseLauncher):
            def __init__(self):
                pass

            def __call__(self):
                pass

            def command(self):
                return 'dummy-app'

        launcher = MinimalLauncher()


def requires_command(command):
    """A decorator to skip a test if the executible command is not available."""
    return unittest.skipUnless(shutil.which(command), f'requires {command}')


class TestLauncherBase(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('exit\n')  # Dummy script, simply exits.
        self.script_path = f.name
        self.addCleanup(lambda: os.remove(self.script_path))


@requires_command('gnome-terminal')
class TestGnomeTerminalLauncher(TestLauncherBase):
    def test_find_gnome_terminal_server(self):
        result = GnomeTerminalLauncher._find_gnome_terminal_server()
        self.assertIsNotNone(result)
        self.assertRegex(result, 'gnome-terminal-server$')

    def test_name_has_owner(self):
        result = GnomeTerminalLauncher.name_has_owner('unknown.name.with.no.owner')
        self.assertFalse(result)

        current_desktop = os.environ.get('XDG_CURRENT_DESKTOP')
        if current_desktop == 'GNOME':
            result = GnomeTerminalLauncher.name_has_owner('org.gnome.Shell')
        elif current_desktop == 'KDE':
            result = GnomeTerminalLauncher.name_has_owner('org.kde.KWin')
        self.assertTrue(result)

    def test_call_launcher(self):
        launcher = GnomeTerminalLauncher(self.script_path)
        process = launcher()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)


@requires_command('yakuake')
class TestYakuakeLauncher(TestLauncherBase):
    @staticmethod
    def _hide_yakuake_window():
        """Make D-Bus call to hide Yakuake window."""
        subprocess.run([
            'dbus-send',
            '--type=method_call',
            '--dest=org.kde.yakuake',
            '/yakuake/MainWindow_1',
            'org.qtproject.Qt.QWidget.hide',
        ])

    def test_yakuake(self):
        self.addCleanup(self._hide_yakuake_window)

        launch = YakuakeLauncher(self.script_path)
        returncode = launch()
        time.sleep(0.1)  # <- TODO: Remove after fixing process handling.
        self.assertEqual(returncode, 0)


class TestSimpleLaunchers(TestLauncherBase):
    @requires_command('alacritty')
    def test_alacritty(self):
        launch = AlacrittyLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('cool-retro-term')
    def test_cool_retro_term(self):
        launch = CoolRetroTermLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('guake')
    def test_guake(self):
        launch = GuakeLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)
        time.sleep(0.1)
        subprocess.run(['guake', '--hide'])

    @requires_command('kitty')
    def test_kitty(self):
        launch = KittyLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('konsole')
    def test_konsole(self):
        launch = KonsoleLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('qterminal')
    def test_qterminal(self):
        launch = QTerminalLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('sakura')
    def test_sakura(self):
        launch = SakuraLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('terminator')
    def test_terminator(self):
        launch = TerminatorLauncher(self.script_path)
        process = launch()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('xfce4-terminal')
    def test_xfce4terminal(self):
        launcher = Xfce4Terminal(self.script_path)
        process = launcher()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)

    @requires_command('xterm')
    def test_xterm(self):
        launcher = XTermLauncher(self.script_path)
        process = launcher()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)
