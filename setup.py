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

import setuptools


def get_long_description(readmepath):
    with open(readmepath) as file:
        long_description = file.read()
    return long_description


if __name__ == '__main__':
    setuptools.setup(
        # Required fields:
        name='EnvLauncher',
        version='0.1a1.dev1',
        description=('A GNOME desktop launcher to activate Python '
                     'development environments.'),
        py_modules=['envlauncher'],

        # Recommended fields:
        url='https://github.com/shawnbrown/envlauncher',
        author='Shawn Brown',
        author_email='shawnbrown@users.noreply.github.com',

        # Other fields:
        long_description=get_long_description('README.md'),
        long_description_content_type='text/markdown',
        entry_points={
            'console_scripts': [
                'envlauncher = envlauncher:launch_environment',
            ],
        },
        install_requires=[],  # <- No additional dependencies!
        python_requires='>=3.6',
        license='GNU General Public License v3 (GPLv3)',
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Topic :: Desktop Environment :: Gnome',
            'Topic :: Software Development',
        ],
    )
