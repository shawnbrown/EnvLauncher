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

"""Tests for EnvLauncher."""

import os
import shutil
import tempfile
import textwrap
import unittest
import envlauncher


class TestDataPathsAttributes(unittest.TestCase):
    def test_data_home(self):
        datapaths = envlauncher.DataPaths({
            'XDG_DATA_HOME': '/other/location/share',
            'HOME': '/home/testuser',
        })
        self.assertEqual(datapaths.data_home, '/other/location/share')

    def test_data_home_default(self):
        datapaths = envlauncher.DataPaths({
            'HOME': '/home/testuser',
        })
        self.assertEqual(datapaths.data_home, '/home/testuser/.local/share')

    def test_data_dirs(self):
        datapaths = envlauncher.DataPaths({
            'HOME': '/home/testuser',
            'XDG_DATA_DIRS': '/foo/bar:/var/lib/baz',
        })
        self.assertEqual(datapaths.data_dirs, ['/foo/bar', '/var/lib/baz'])

    def test_data_dirs_default(self):
        datapaths = envlauncher.DataPaths({
            'HOME': '/home/testuser',
        })
        self.assertEqual(datapaths.data_dirs, ['/usr/local/share', '/usr/share'])


class DataPathsFindResourcePath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Define temporary directory structure and files.
        temporary_structure = {
            'highest/preference/applications': [
                'app1.desktop',  # <- Present in highest, middle, and lowest.
            ],
            'middle/preference/applications': [
                'app1.desktop',
                'app2.desktop',  # <- Present in middle and lowest.
            ],
            'lowest/preference/applications': [
                'app1.desktop',
                'app2.desktop',
                'app3.desktop',  # <- Present in lowest only.
            ],
        }

        # Create temporary directory structure and files.
        cls.tempdir = tempfile.TemporaryDirectory()
        tempname = cls.tempdir.name
        for directory, filenames in temporary_structure.items():
            os.makedirs(os.path.join(tempname, directory))
            for name in filenames:
                filepath = os.path.join(tempname, directory, name)
                with open(filepath, 'w') as fh:
                    fh.write('dummy file contents')

        # Create a DataPaths instance with a custom environ.
        cls.datapaths = envlauncher.DataPaths({
            'XDG_DATA_HOME': os.path.join(tempname, 'highest/preference'),
            'XDG_DATA_DIRS': ':'.join([
                os.path.join(tempname, 'middle/preference'),
                os.path.join(tempname, 'lowest/preference'),
            ])
        })

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def test_highest_preference(self):
        filepath = self.datapaths.find_resource_path('applications', 'app1.desktop')
        regex = r'/highest/preference/applications/app1[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_middle_preference(self):
        filepath = self.datapaths.find_resource_path('applications', 'app2.desktop')
        regex = r'/middle/preference/applications/app2[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_lowest_preference(self):
        filepath = self.datapaths.find_resource_path('applications', 'app3.desktop')
        regex = r'/lowest/preference/applications/app3[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_no_matching_file(self):
        with self.assertRaises(FileNotFoundError):
            self.datapaths.find_resource_path('applications', 'app4.desktop')


class DataPathsMakeHomePath(unittest.TestCase):
    def test_home_filepath(self):
        datapaths = envlauncher.DataPaths({
            'XDG_DATA_HOME': os.path.join('/base/directory'),
        })
        filepath = datapaths.make_home_path('applications', 'app1.desktop')
        expected = '/base/directory/applications/app1.desktop'
        self.assertEqual(filepath, expected)


class TestSettingsEscaping(unittest.TestCase):
    """Since ConfigParser discards comments and extra empty lines,
    we need to escape these lines so we can preserve them when
    saving the config file.

    From the XDG Desktop Entry Specification (version 1.5):

      "Lines beginning with a # and blank lines are considered
      comments and will be ignored, however they should be
      preserved across reads and writes of the desktop entry
      file."
    """

    def setUp(self):
        prefix = envlauncher.Settings._escape_prefix
        suffix = envlauncher.Settings._escape_suffix

        self.unescaped = textwrap.dedent("""
            [Desktop Entry]
            Type=Application


            Exec=gnome-terminal
            #Keywords=hello;world; <- A COMMENT!
        """).lstrip()

        self.escaped = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            {prefix}3{suffix}
            {prefix}4{suffix}
            Exec=gnome-terminal
            {prefix}6{suffix}#Keywords=hello;world; <- A COMMENT!
        """).lstrip()

    def test_prefix_and_suffix(self):
        prefix = envlauncher.Settings._escape_prefix
        suffix = envlauncher.Settings._escape_suffix

        self.assertNotIn(suffix, prefix, msg='Suffix must not be a substring of prefix.')
        self.assertEqual(suffix.count('='), 1, msg='Must contain one equals sign.')
        self.assertNotEqual(suffix[0], '=', msg='Equals sign must not be first character.')
        self.assertNotEqual(suffix[-1], '=', msg='Equals sign must not be last character.')

    def test_escape_comments(self):
        """Should escape comments and blank lines."""
        escaped = envlauncher.Settings._escape_comments(self.unescaped)
        self.assertEqual(escaped, self.escaped)

    def test_unescape_comments(self):
        """Should escape comments and blank lines."""
        unescaped = envlauncher.Settings._unescape_comments(self.escaped)
        self.assertEqual(unescaped, self.unescaped)

    def test_roundtrip(self):
        escaped = envlauncher.Settings._escape_comments(self.unescaped)
        unescaped = envlauncher.Settings._unescape_comments(escaped)
        self.assertEqual(unescaped, self.unescaped)


class TestSettingsFormatting(unittest.TestCase):
    """Make sure parser preserves desktop entry format."""
    @staticmethod
    def textformat(string):  # <- Helper method.
        """Format string for ConfigParser compatibility."""
        return textwrap.dedent(string).lstrip()

    def test_unchanged(self):
        """Check that parser exports keys as given (preserves case)
        and maintains format (no space around the "=" delimeter).
        """
        desktop_entry = self.textformat("""
            [Desktop Entry]
            Type=Application
            Name=Hello World
            Exec=gnome-terminal -- bash -c "echo Hello World;bash"
        """)

        parser = envlauncher.Settings.from_string(desktop_entry)
        export = parser.export_string()
        self.assertEqual(export, desktop_entry, msg='should match original')

    def test_preserve_comments(self):
        """Comments should be preserved, too."""
        desktop_entry = self.textformat("""
            [Desktop Entry]
            Type=Application
            Name=Hello World
            Exec=gnome-terminal -- bash -c "echo Hello World;bash"
            #Keywords=hello;world; <- A COMMENT!
        """)

        parser = envlauncher.Settings.from_string(desktop_entry)
        export = parser.export_string()
        self.assertEqual(export, desktop_entry)

    def test_preserve_duplicate_comments_and_whitespace(self):
        """Duplicate comments and whitespace should also be preserved."""
        desktop_entry = self.textformat("""
            [Desktop Entry]
            Type=Application


            #Foo
            #Foo
            Name=Hello World
            Exec=gnome-terminal -- bash -c "echo Hello World;bash"
        """)

        parser = envlauncher.Settings.from_string(desktop_entry)
        export = parser.export_string()
        self.assertEqual(export, desktop_entry)


class TestSettingsRcfile(unittest.TestCase):
    def setUp(self):
        desktop_entry = textwrap.dedent("""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application

            [X-EnvLauncher Options]
            Rcfile=~/.bashrc
        """).lstrip()
        self.settings = envlauncher.Settings.from_string(desktop_entry)

    def test_read(self):
        self.assertEqual(self.settings.rcfile, '~/.bashrc')

    def test_set_value(self):
        self.settings.rcfile = '.venvrc'
        self.assertEqual(self.settings.rcfile, '.venvrc')

    def test_invalid_value(self):
        self.settings.rcfile = 1234  # <- Bogus value.
        self.assertEqual(self.settings.rcfile, '')  # <- Empty string.


class TestSettingsTerminalEmulator(unittest.TestCase):
    def setUp(self):
        desktop_entry = textwrap.dedent("""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application

            [X-EnvLauncher Options]
            TerminalEmulator=gnome-terminal
        """).lstrip()
        self.settings = envlauncher.Settings.from_string(desktop_entry)

    def test_available(self):
        """If TerminalEmulator in settings is available, it should be
        available via `terminal_emulator` attribute.
        """
        self.settings._terminal_emulator_choices = ['guake', 'gnome-terminal']
        self.assertEqual(self.settings.terminal_emulator, 'gnome-terminal')

    def test_not_available(self):
        """If TerminalEmulator in settings is not available, the
        `terminal_emulator` property should return the first available
        item from `terminal_emulator_choices`.
        """
        self.settings._terminal_emulator_choices = ['konsole', 'yakuake']
        self.assertEqual(self.settings.terminal_emulator, 'konsole')


class TestSettingsBanner(unittest.TestCase):
    def setUp(self):
        desktop_entry = textwrap.dedent("""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application

            [X-EnvLauncher Options]
            Banner=color
        """).lstrip()
        self.settings = envlauncher.Settings.from_string(desktop_entry)

    def test_read(self):
        self.assertEqual(self.settings.banner, 'color')

    def test_set_value(self):
        self.settings.banner = 'plain'
        self.assertEqual(self.settings.banner, 'plain')

        self.settings.banner = 'none'
        self.assertEqual(self.settings.banner, 'none')

    def test_invalid_value(self):
        self.settings.banner = 1234  # <- Bogus value.
        self.assertEqual(self.settings.banner, 'color')  # <- Defaults to color.

    def test_banner_resource(self):
        self.assertEqual(self.settings.banner_resource,
                         ('envlauncher', 'banner-color.ascii'))

        self.settings.banner = 'plain'
        self.assertEqual(self.settings.banner_resource,
                         ('envlauncher', 'banner-plain.ascii'))

        self.settings.banner = 'none'
        self.assertIsNone(self.settings.banner_resource)


class TestSettingsMakeIdentifier(unittest.TestCase):
    def test_no_existing_venv_actions(self):
        prefix = envlauncher.Settings._venv_prefix
        desktop_entry = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
            Actions=configure;
        """)
        settings = envlauncher.Settings.from_string(desktop_entry)
        self.assertEqual(settings.make_identifier(), f'{prefix}1')
        self.assertEqual(settings.make_identifier(), f'{prefix}2')
        self.assertEqual(settings.make_identifier(), f'{prefix}3')

    def test_has_existing_venv_actions(self):
        prefix = envlauncher.Settings._venv_prefix
        desktop_entry = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
            Actions={prefix}2;configure;
        """)
        settings = envlauncher.Settings.from_string(desktop_entry)
        self.assertEqual(settings.make_identifier(), f'{prefix}1')
        self.assertEqual(settings.make_identifier(), f'{prefix}3',
                         msg='skips 2 since "venv2" already exists')
        self.assertEqual(settings.make_identifier(), f'{prefix}4')


class TestSettingsGetActions(unittest.TestCase):
    def setUp(self):
        self.prefix = envlauncher.Settings._venv_prefix
        desktop_entry = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
            Actions={self.prefix}1;{self.prefix}2;configure;

            [Desktop Action {self.prefix}1]
            Name=Python 3.9
            Exec=envlauncher --activate "~/.venv39/bin/activate" --directory "~/Projects/"

            [Desktop Action {self.prefix}2]
            Name=Python 2.7
            Exec=envlauncher --activate "~/.venv27/bin/activate" --directory "~/Projects/legacy/"

            [Desktop Action configure]
            Name=Configure EnvLauncher
            Exec=envlauncher --configure
        """).lstrip()
        self.settings = envlauncher.Settings.from_string(desktop_entry)

    def test_basic_behavior(self):
        actual = self.settings.get_actions()
        expected = [
            (f'{self.prefix}1', 'Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
            (f'{self.prefix}2', 'Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
        ]
        self.assertEqual(actual, expected)

    def test_mismatched_actions_and_groups(self):
        """The Actions value includes "venv3" but there is no matching group.
        The method should return the existing groups without errors.
        """
        prefix = self.prefix

        self.settings._parser['Desktop Entry']['Actions'] = f'{prefix}1;{prefix}2;{prefix}3;configure;'
        actual = self.settings.get_actions()
        expected = [
            (f'{prefix}1', 'Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
            (f'{prefix}2', 'Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
        ]
        self.assertEqual(actual, expected)

    def test_actions_value_order(self):
        """Actions should be returned in the order they are listed in
        the Desktop Entry's Actions value.
        """
        prefix = self.prefix

        # Action identifiers are in a different order ("venv2" before "venv1").
        self.settings._parser['Desktop Entry']['Actions'] = f'{prefix}2;{prefix}1;configure;'
        actual = self.settings.get_actions()
        expected = [
            (f'{prefix}2', 'Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
            (f'{prefix}1', 'Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
        ]
        self.assertEqual(actual, expected)

    def test_missing_actions_section(self):
        """Should still work when "Actions" key and action groups missing."""
        desktop_entry = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
        """).lstrip()
        settings = envlauncher.Settings.from_string(desktop_entry)
        self.assertEqual(settings.get_actions(), [])


class TestSettingsSetActions(unittest.TestCase):
    def setUp(self):
        desktop_entry = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
            Actions=configure;

            [Desktop Action configure]
            Name=Configure EnvLauncher
            Exec=envlauncher --configure
        """).lstrip()
        self.settings = envlauncher.Settings.from_string(desktop_entry)
        self.prefix = envlauncher.Settings._venv_prefix

    def test_set_actions(self):
        prefix = self.prefix
        actions = [
            (f'{prefix}1', 'Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
            (f'{prefix}2', 'Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
        ]
        self.settings.set_actions(actions)

        action_values = self.settings._parser['Desktop Entry']['Actions']
        self.assertEqual(action_values, f'{prefix}1;{prefix}2;configure;')

        actual_venv_groups = [
            self.settings._parser[f'Desktop Action {prefix}1'],
            self.settings._parser[f'Desktop Action {prefix}2'],
        ]
        expected_venv_groups = [
            {'Name': 'Python 3.9',
             'Exec': 'envlauncher --activate "~/.venv39/bin/activate" --directory "~/Projects/"'},
            {'Name': 'Python 2.7',
             'Exec': 'envlauncher --activate "~/.venv27/bin/activate" --directory "~/Projects/legacy/"'},
        ]
        self.assertEqual(actual_venv_groups, expected_venv_groups)

    def test_arbitrary_action_groups(self):
        """Non-venv action groups should be preserved between updates."""
        prefix = self.prefix
        desktop_entry = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
            Actions=other;{prefix}3;configure;

            [Desktop Action other]
            Name=Other Action
            Exec=envlauncher --configure

            [Desktop Action {self.prefix}3]
            Name=Python 3.10
            Exec=envlauncher --activate "~/.venv310/bin/activate" --directory "~/Projects/"

            [Desktop Action configure]
            Name=Configure EnvLauncher
            Exec=envlauncher --configure
        """).lstrip()
        settings = envlauncher.Settings.from_string(desktop_entry)
        settings.set_actions([
            (f'{prefix}1', 'Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
            (f'{prefix}2', 'Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
        ])

        self.assertEqual(
            settings._parser['Desktop Entry']['Actions'],
            f'{prefix}1;{prefix}2;other;configure;',
            msg='should preserve "other" and "configure" identifiers',
        )

        self.assertEqual(
            settings._parser.sections(),
            [
                'Desktop Entry',
                'Desktop Action other',
                'Desktop Action configure',
                f'Desktop Action {prefix}1',
                f'Desktop Action {prefix}2',
            ],
            msg='should preserve "other" and "configure" groups',
        )

    def test_missing_actions_section(self):
        """Should still work when "Actions" key and action groups missing."""
        prefix = self.prefix
        desktop_entry = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
        """).lstrip()
        settings = envlauncher.Settings.from_string(desktop_entry)
        settings.set_actions([
            (f'{prefix}1', 'Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
            (f'{prefix}2', 'Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
        ])

        export = settings.export_string()
        expected = textwrap.dedent(f"""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --configure
            Type=Application
            Actions={prefix}1;{prefix}2;

            [Desktop Action {prefix}1]
            Name=Python 3.9
            Exec=envlauncher --activate "~/.venv39/bin/activate" --directory "~/Projects/"

            [Desktop Action {prefix}2]
            Name=Python 2.7
            Exec=envlauncher --activate "~/.venv27/bin/activate" --directory "~/Projects/legacy/"
        """).lstrip()
        self.assertEqual(export, expected)
