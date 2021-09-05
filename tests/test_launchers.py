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

import subprocess
import unittest
from envlauncher.launchers import BaseLauncher


class TestBaseLauncher(unittest.TestCase):
    def test_minimal_launcher(self):
        """Test abstract base class with dummy concrete class."""

        class MinimalLauncher(BaseLauncher):
            def __init__(self):
                pass

            def __call__(self):
                process = subprocess.Popen(['true', 'dummy', 'command'])
                process.wait()  # Wait until subprocess completes.
                return process

        launcher = MinimalLauncher()
        return_val = launcher()
        self.assertIsInstance(return_val, subprocess.Popen)
