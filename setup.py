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

"""EnvLauncher: Launch Python development environments."""

import sys
if sys.version_info < (3, 6):
    # A few older Linux distributions that are still supported (but
    # nearing end-of-life) still ship with versions of Python whose
    # installation tools do not enforce the `python_requires` argument.
    error_message = (
        "ERROR:\n"
        "  Package 'envlauncher' requires Python 3.6 or newer\n"
        "  but installation was attempted using Python {0}.{1}.\n"
    ).format(*sys.version_info[:2])
    sys.stderr.write(error_message)
    sys.exit(1)


try:
    from distutils.core import setup
except (ModuleNotFoundError, ImportError) as error:
    error.msg = """{0}

    Your system does not appear to have the full `distutils` package.
    In Python versions 3.11 and earlier, `distutils` is part of the
    Standard Library (see PEP 632) but certain Linux distributions are
    shipped with a minimal install of Python that omits some standard
    packages.

    The use of `setuptools` is recommended over `distustils` but
    either one is sufficient. You should be able to install one of
    these packages using your system's package manager.

    For Debian or Debian-based distributions (like Ubuntu, Mint,
    Pop!_OS, etc.), you can use one of the following commands:

        sudo apt install python3-setuptools

        or

        sudo apt install python3-distutils
    """.format(error.msg)
    raise error


def get_version(path):
    """Return value of path's __version__ attribute."""
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('__version__'):
                _, _, value = line.partition('=')
                return value.strip(' \'"')
    raise Exception('Unable to find __version__ attribute.')


def get_long_description(readmepath):
    with open(readmepath) as file:
        long_description = file.read()
    return long_description


if __name__ == '__main__':
    setup(
        # Required fields:
        name='EnvLauncher',
        version=get_version('envlauncher/app.py'),
        description=(
            'A Linux desktop launcher for Python virtual '
            'environments (supports GNOME, KDE, and more).'
        ),
        packages=['envlauncher'],

        # Recommended fields:
        url='https://github.com/shawnbrown/envlauncher',
        author='Shawn Brown',
        author_email='shawnbrown@users.noreply.github.com',

        # Other fields:
        long_description=get_long_description('README.md'),
        long_description_content_type='text/markdown',
        scripts=['bin/envlauncher'],
        data_files = [
            ('share/applications', ['data/com.github.shawnbrown.EnvLauncher.desktop']),
            ('share/envlauncher', ['data/envlauncher/banner-color.ascii',
                                   'data/envlauncher/banner-plain.ascii']),
            # Fallback/default icons used by GNOME environment.
            ('share/icons/hicolor/scalable/apps', ['data/hicolor/com.github.shawnbrown.EnvLauncher.svg']),
            ('share/icons/hicolor/symbolic/apps', ['data/hicolor/com.github.shawnbrown.EnvLauncher-symbolic.svg']),
            # Icons for default Ubuntu theme.
            ('share/icons/Yaru/48x48/apps', ['data/Yaru/48x48/com.github.shawnbrown.EnvLauncher.svg']),
            ('share/icons/Yaru/scalable/apps', ['data/Yaru/scalable/com.github.shawnbrown.EnvLauncher.svg',
                                                'data/Yaru/scalable/com.github.shawnbrown.EnvLauncher-symbolic.svg']),
        ],
        install_requires=[],  # <- No additional dependencies!
        python_requires='>=3.6',
        license='GNU General Public License v3 (GPLv3)',
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Topic :: Desktop Environment :: Gnome',
            'Topic :: Software Development',
        ],
    )
