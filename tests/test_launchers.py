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
import unittest
from envlauncher.launchers import BaseLauncher
from envlauncher.launchers import GnomeTerminalLauncher
from envlauncher.launchers import XTermLauncher


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

    def test_minimal_subclass(self):
        """Minimal concrete class definition."""
        class MinimalLauncher(BaseLauncher):
            def __init__(self):
                pass

            def __call__(self):
                pass

        launcher = MinimalLauncher()


class TestLauncherBase(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('exit\n')  # Dummy script, simply exits.
        self.script_path = f.name
        self.addCleanup(lambda: os.remove(self.script_path))


@unittest.skipUnless(shutil.which('gnome-terminal'), 'requires gnome-terminal')
class TestGnomeTerminalLauncher(TestLauncherBase):
    def test_find_gnome_terminal_server(self):
        result = GnomeTerminalLauncher._find_gnome_terminal_server()
        self.assertIsNotNone(result)
        self.assertRegex(result, 'gnome-terminal-server$')

    def test_name_has_owner(self):
        result = GnomeTerminalLauncher.name_has_owner('unknown.name.with.no.owner')
        self.assertFalse(result)

        result = GnomeTerminalLauncher.name_has_owner('org.gnome.Shell')
        self.assertTrue(result)

    def test_call_launcher(self):
        launcher = GnomeTerminalLauncher(self.script_path)
        process = launcher()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)


class TestSimpleLaunchers(TestLauncherBase):
    @unittest.skipUnless(shutil.which('xterm'), 'requires xterm')
    def test_xterm(self):
        launcher = XTermLauncher(self.script_path)
        process = launcher()
        process.wait(timeout=5)
        self.assertEqual(process.returncode, 0)
