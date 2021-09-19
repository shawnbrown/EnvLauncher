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

"""Main function for EnvLauncher."""

from .app import __version__
from .app import DataPaths
from .app import EnvLauncherApp
from .app import configure_envlauncher
from .cli import parse_args


def main():
    args = parse_args()
    if args.activate:
        launcher = EnvLauncherApp()
        launcher(args.activate, args.directory)
    elif args.configure:
        paths = DataPaths()
        configure_envlauncher(paths, args.reset_all)
    elif args.version:
        print(__version__)
