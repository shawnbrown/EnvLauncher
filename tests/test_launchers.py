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
    def test_required_methods(self):
        methods = BaseLauncher.__abstractmethods__
        self.assertEqual(methods, {'__init__', '__call__', 'command'})

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


@requires_command('gnome-terminal')
class TestGnomeTerminalHelperMethods(unittest.TestCase):
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


class TestYakuakeHelperMethods(unittest.TestCase):
    def test_build_args(self):
        args = YakuakeLauncher.build_args(
            '/yakuake/tabs',
            'setTabTitle',
            f'int32:7',
            'string:EnvLauncher',
        )
        expected = [
            'dbus-send',
            '--session',
            '--dest=org.kde.yakuake',
            '--print-reply=literal',
            '--type=method_call',
            '/yakuake/tabs',
            'org.kde.yakuake.setTabTitle',
            'int32:7',
            'string:EnvLauncher',
        ]
        self.assertEqual(args, expected)

    def test_parse_session_id(self):
        session_id = YakuakeLauncher.parse_session_id(b'   int32 7')
        self.assertEqual(session_id, 7)


class TestTerminalEmulators(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('exit\n')  # Dummy script, simply exits.
        self.script_path = f.name
        self.addCleanup(lambda: os.remove(self.script_path))

    def assertReturnCode(self, obj, expected):
        """Check that the return code from *obj* matches the *expected*
        value.

        Args:
            obj (Popen | int): A process object or return code to check.
            expected (int): The expected integer return code.
        """
        if hasattr(obj, 'wait'):
            obj.wait(timeout=5)
            obj = obj.returncode
        self.assertEqual(obj, expected)

    @requires_command('alacritty')
    def test_alacritty(self):
        launch = AlacrittyLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('cool-retro-term')
    def test_cool_retro_term(self):
        launch = CoolRetroTermLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('gnome-terminal')
    def test_gnome_terminal(self):
        launcher = GnomeTerminalLauncher(self.script_path)
        process = launcher()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('guake')
    def test_guake(self):
        def hide_window():  # <- Helper function to close Guake window.
            time.sleep(0.1)
            subprocess.run(['guake', '--hide'])

        self.addCleanup(hide_window)

        launch = GuakeLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('kitty')
    def test_kitty(self):
        launch = KittyLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('konsole')
    def test_konsole(self):
        launch = KonsoleLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('qterminal')
    def test_qterminal(self):
        launch = QTerminalLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('sakura')
    def test_sakura(self):
        launch = SakuraLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('terminator')
    def test_terminator(self):
        launch = TerminatorLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('xfce4-terminal')
    def test_xfce4terminal(self):
        launcher = Xfce4Terminal(self.script_path)
        process = launcher()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('xterm')
    def test_xterm(self):
        launcher = XTermLauncher(self.script_path)
        process = launcher()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('yakuake')
    def test_yakuake(self):
        def hide_window():  # <- Helper function to close Yakuake window.
            time.sleep(0.1)
            subprocess.run([
                'dbus-send',
                '--type=method_call',
                '--dest=org.kde.yakuake',
                '/yakuake/MainWindow_1',
                'org.qtproject.Qt.QWidget.hide',
            ])

        self.addCleanup(hide_window)

        launch = YakuakeLauncher(self.script_path)
        result = launch()
        self.assertReturnCode(result, os.EX_OK)
