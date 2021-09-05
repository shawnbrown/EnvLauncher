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
