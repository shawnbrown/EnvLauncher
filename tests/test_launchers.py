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
from envlauncher import launchers


def is_available(command):
    """Return True if *command* is available."""
    return shutil.which(command) is not None


def requires_command(command):
    """A decorator to skip a test if the executible command is not available."""
    return unittest.skipUnless(is_available(command), f'requires {command}')


# Determine visibility of the Yakuake console before testing begins.
if is_available('yakuake'):
    YAKUAKE_NOT_VISIBLE = not launchers.YakuakeLauncher.is_visible()
else:
    YAKUAKE_NOT_VISIBLE = True


class TestAbstractBaseLauncher(unittest.TestCase):
    def test_required_methods_and_attributes(self):
        methods = launchers.BaseLauncher.__abstractmethods__
        self.assertEqual(methods, {'__init__', '__call__'})

    def test_missing_attribute(self):
        """Since `command` is not defined, should raise error"""
        with self.assertRaises(TypeError):
            # Subclasses must also have "command" class attribute.
            class IncompleteLauncher(launchers.BaseLauncher):
                def __init__(self_):
                    pass

                def __call__(self_):
                    pass

    def test_minimal_subclass(self):
        """Minimal concrete class definition."""
        class MinimalLauncher(launchers.BaseLauncher):
            command = 'dummy-app'

            def __init__(self_):
                pass

            def __call__(self_):
                pass

        launcher = MinimalLauncher()


class TestLauncherClassNames(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        launcher_classes = []
        for obj in launchers.__dict__.values():
            if not isinstance(obj, type):
                continue
            if not issubclass(obj, launchers.BaseLauncher):
                continue
            if obj is launchers.BaseLauncher:
                continue
            launcher_classes.append(obj)

        cls.launcher_classes = launcher_classes

    def test_get_class_name(self):
        self.assertEqual(launchers.get_class_name('foo'), 'FooLauncher')
        self.assertEqual(launchers.get_class_name('BAR'), 'BarLauncher')
        self.assertEqual(launchers.get_class_name('foo-bar'), 'FooBarLauncher')

    def test_class_name_command_agreement(self):
        """Launcher names should be derived from their command strings.
        For example, the launcher class for "gnome-terminal" needs to
        be named "GnomeTerminalLauncher". This test checks that all
        concrete launcher names correspond to their command string
        values.
        """
        for launcher_cls in self.launcher_classes:
            # Name of this launcher class.
            cls_name = launcher_cls.__name__

            # Generated name (based on `launcher_cls.command` value).
            required_name = launchers.get_class_name(launcher_cls.command)

            with self.subTest(command=launcher_cls.command):
                msg = f'Class name needs to be {required_name}.'
                self.assertEqual(cls_name, required_name, msg=msg)


@requires_command('gnome-terminal')
class TestGnomeTerminalHelperMethods(unittest.TestCase):
    def test_find_gnome_terminal_server(self):
        result = launchers.GnomeTerminalLauncher._find_gnome_terminal_server()
        self.assertIsNotNone(result)
        self.assertRegex(result, 'gnome-terminal-server$')

    def test_name_has_owner(self):
        name_has_owner = launchers.GnomeTerminalLauncher.name_has_owner

        result = name_has_owner('unknown.name.with.no.owner')
        self.assertFalse(result)

        current_desktop = os.environ.get('XDG_CURRENT_DESKTOP')
        if current_desktop == 'GNOME':
            result = name_has_owner('org.gnome.Shell')
        elif current_desktop == 'KDE':
            result = name_has_owner('org.kde.KWin')
        self.assertTrue(result)


@requires_command('yakuake')
class TestYakuakeHelperMethods(unittest.TestCase):
    def test_build_args_unqualified(self):
        args = launchers.YakuakeLauncher.build_args(
            '/yakuake/tabs',
            'setTabTitle',  # <- Unqualified method name.
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
            'org.kde.yakuake.setTabTitle',  # <- Gets 'org.kde.yakuake' interface.
            'int32:7',
            'string:EnvLauncher',
        ]
        self.assertEqual(args, expected)

    def test_build_args_qualified(self):
        args = launchers.YakuakeLauncher.build_args(
            '/yakuake/MainWindow_1',
            'org.freedesktop.DBus.Properties.Get',  # <- Fully qualified name.
            'string:org.qtproject.Qt.QWidget',
            'string:visible',
        )
        expected = [
            'dbus-send',
            '--session',
            '--dest=org.kde.yakuake',
            '--print-reply=literal',
            '--type=method_call',
            '/yakuake/MainWindow_1',
            'org.freedesktop.DBus.Properties.Get',  # <- Returned unchanged.
            'string:org.qtproject.Qt.QWidget',
            'string:visible'
        ]
        self.assertEqual(args, expected)

    def test_parse_session_id(self):
        session_id = launchers.YakuakeLauncher.parse_session_id(b'   int32 7')
        self.assertEqual(session_id, 7)

    def test_is_visible(self):
        result = launchers.YakuakeLauncher.is_visible()
        self.assertIsInstance(result, bool)


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
        launch = launchers.AlacrittyLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('cool-retro-term')
    def test_cool_retro_term(self):
        launch = launchers.CoolRetroTermLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('gnome-terminal')
    def test_gnome_terminal(self):
        launcher = launchers.GnomeTerminalLauncher(self.script_path)
        process = launcher()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('guake')
    def test_guake(self):
        def hide_window():  # <- Helper function to close Guake window.
            time.sleep(0.1)
            subprocess.run(['guake', '--hide'])

        self.addCleanup(hide_window)

        launch = launchers.GuakeLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('kitty')
    def test_kitty(self):
        launch = launchers.KittyLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('konsole')
    def test_konsole(self):
        launch = launchers.KonsoleLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('qterminal')
    def test_qterminal(self):
        launch = launchers.QterminalLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('sakura')
    def test_sakura(self):
        launch = launchers.SakuraLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('st')
    def test_st(self):
        launch = launchers.StLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('terminator')
    def test_terminator(self):
        launch = launchers.TerminatorLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('urxvt')
    def test_urxvt(self):
        launch = launchers.UrxvtLauncher(self.script_path)
        process = launch()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('xfce4-terminal')
    def test_xfce4terminal(self):
        launcher = launchers.Xfce4TerminalLauncher(self.script_path)
        process = launcher()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('xterm')
    def test_xterm(self):
        launcher = launchers.XtermLauncher(self.script_path)
        process = launcher()
        self.assertReturnCode(process, os.EX_OK)

    @requires_command('yakuake')
    def test_yakuake(self):
        if YAKUAKE_NOT_VISIBLE:
            # If the Yakuake console is not visible when testing begins,
            # then make sure to hide it when testing finishes.
            def hide_window():
                time.sleep(0.1)
                subprocess.run([
                    'dbus-send',
                    '--type=method_call',
                    '--dest=org.kde.yakuake',
                    '/yakuake/MainWindow_1',
                    'org.qtproject.Qt.QWidget.hide',
                ])

            self.addCleanup(hide_window)
        else:
            # If Yakuake is already visible before testing begins, then
            # don't hide it when testing finishes.
            pass

        launch = launchers.YakuakeLauncher(self.script_path)
        result = launch()
        self.assertReturnCode(result, os.EX_OK)
