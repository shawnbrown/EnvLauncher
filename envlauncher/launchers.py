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
import subprocess
from typing import Optional


class BaseLauncher(abc.ABC):
    """Base class for terminal emulator launchers."""
    app_id = 'com.github.shawnbrown.EnvLauncher'

    @abc.abstractmethod
    def __init__(self, script_path):
        """Initialize launcher class."""
        self.script_path = script_path  #: File path of activation script.
        self.command = NotImplemented  #: Name of terminal emulator command.

    @abc.abstractmethod
    def __call__(self) -> Optional[subprocess.Popen]:
        """Start terminal emulator and run activation script."""
        raise NotImplementedError
