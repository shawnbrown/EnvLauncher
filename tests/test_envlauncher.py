"""Tests for EnvLauncher."""
import contextlib
import io
import os
import tempfile
import textwrap
import unittest
import envlauncher


class TestParseArgs(unittest.TestCase):
    def setUp(self):
        self.exit_message = io.StringIO()
        redirect = contextlib.redirect_stderr(self.exit_message)
        redirect.__enter__()
        self.addCleanup(lambda: redirect.__exit__(None, None, None))

    def test_no_args(self):
        args = envlauncher.parse_args([])
        self.assertEqual(args.activate, None)
        self.assertEqual(args.directory, None)
        self.assertEqual(args.preferences, False)
        self.assertEqual(args.reset_all, False)

    def test_activate(self):
        args = envlauncher.parse_args(['--activate', 'myscript'])
        self.assertEqual(args.activate, 'myscript')
        self.assertEqual(args.directory, None)
        self.assertEqual(args.preferences, False)
        self.assertEqual(args.reset_all, False)

    def test_activate_directory(self):
        args = envlauncher.parse_args(['--activate', 'myscript', '--directory', 'mydir'])
        self.assertEqual(args.activate, 'myscript')
        self.assertEqual(args.directory, 'mydir')
        self.assertEqual(args.preferences, False)
        self.assertEqual(args.reset_all, False)

    def test_directory(self):
        with self.assertRaises(SystemExit):
            args = envlauncher.parse_args(['--directory', 'mydir'])

        self.assertIn(
            'argument --activate is required when using --directory',
            self.exit_message.getvalue(),
        )

    def test_preferences(self):
        args = envlauncher.parse_args(['--preferences'])
        self.assertEqual(args.activate, None)
        self.assertEqual(args.directory, None)
        self.assertEqual(args.preferences, True)
        self.assertEqual(args.reset_all, False)

    def test_preferences_reset_all(self):
        args = envlauncher.parse_args(['--preferences', '--reset-all'])
        self.assertEqual(args.activate, None)
        self.assertEqual(args.directory, None)
        self.assertEqual(args.preferences, True)
        self.assertEqual(args.reset_all, True)

    def test_reset_all(self):
        with self.assertRaises(SystemExit):
            args = envlauncher.parse_args(['--reset-all'])

        self.assertIn(
            'argument --preferences is required when using --reset-all',
            self.exit_message.getvalue(),
        )

    def test_mutually_exclusive_groups(self):
        with self.assertRaises(SystemExit):
            args = envlauncher.parse_args(['--activate', 'myscript', '--preferences'])

        self.assertIn(
            'argument --activate cannot be used with --preferences',
            self.exit_message.getvalue(),
        )


class TestXDGDataPathsAttributes(unittest.TestCase):
    def test_data_home(self):
        xdgdir = envlauncher.XDGDataPaths({
            'XDG_DATA_HOME': '/other/location/share',
            'HOME': '/home/testuser',
        })
        self.assertEqual(xdgdir.data_home, '/other/location/share')

    def test_data_home_default(self):
        xdgdir = envlauncher.XDGDataPaths({
            'HOME': '/home/testuser',
        })
        self.assertEqual(xdgdir.data_home, '/home/testuser/.local/share')

    def test_data_dirs(self):
        xdgdir = envlauncher.XDGDataPaths({
            'HOME': '/home/testuser',
            'XDG_DATA_DIRS': '/foo/bar:/var/lib/baz',
        })
        self.assertEqual(xdgdir.data_dirs, ['/foo/bar', '/var/lib/baz'])

    def test_data_dirs_default(self):
        xdgdir = envlauncher.XDGDataPaths({
            'HOME': '/home/testuser',
        })
        self.assertEqual(xdgdir.data_dirs, ['/usr/local/share', '/usr/share'])


class XDGDataPathsFindResourcePath(unittest.TestCase):
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

        # Create an XDGDataPaths instance with a custom environ.
        cls.xdgdir = envlauncher.XDGDataPaths({
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
        filepath = self.xdgdir.find_resource_path('applications', 'app1.desktop')
        regex = r'/highest/preference/applications/app1[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_middle_preference(self):
        filepath = self.xdgdir.find_resource_path('applications', 'app2.desktop')
        regex = r'/middle/preference/applications/app2[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_lowest_preference(self):
        filepath = self.xdgdir.find_resource_path('applications', 'app3.desktop')
        regex = r'/lowest/preference/applications/app3[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_no_matching_file(self):
        with self.assertRaises(FileNotFoundError):
            self.xdgdir.find_resource_path('applications', 'app4.desktop')


class XDGDataPathsMakeHomePath(unittest.TestCase):
    def test_home_filepath(self):
        xdgdir = envlauncher.XDGDataPaths({
            'XDG_DATA_HOME': os.path.join('/base/directory'),
        })
        filepath = xdgdir.make_home_path('applications', 'app1.desktop')
        expected = '/base/directory/applications/app1.desktop'
        self.assertEqual(filepath, expected)


class TestDesktopEntryParserEscaping(unittest.TestCase):
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
        prefix = envlauncher.DesktopEntryParser._escape_prefix
        suffix = envlauncher.DesktopEntryParser._escape_suffix

        self.unescaped = textwrap.dedent("""
            [Desktop Entry]
            Type=Application


            Exec=gnome-terminal
            #Keywords=hello;world; <- A COMMENT!
        """).strip()

        self.escaped = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            {prefix}3{suffix}
            {prefix}4{suffix}
            Exec=gnome-terminal
            {prefix}6{suffix}#Keywords=hello;world; <- A COMMENT!
        """).strip()

    def test_prefix_and_suffix(self):
        prefix = envlauncher.DesktopEntryParser._escape_prefix
        suffix = envlauncher.DesktopEntryParser._escape_suffix

        self.assertNotIn(suffix, prefix, msg='Suffix must not be a substring of prefix.')
        self.assertEqual(suffix.count('='), 1, msg='Must contain one equals sign.')
        self.assertNotEqual(suffix[0], '=', msg='Equals sign must not be first character.')
        self.assertNotEqual(suffix[-1], '=', msg='Equals sign must not be last character.')

    def test_escape_comments(self):
        """Should escape comments and blank lines."""
        escaped = envlauncher.DesktopEntryParser._escape_comments(self.unescaped)
        self.assertEqual(escaped, self.escaped)

    def test_unescape_comments(self):
        """Should escape comments and blank lines."""
        unescaped = envlauncher.DesktopEntryParser._unescape_comments(self.escaped)
        self.assertEqual(unescaped, self.unescaped)

    def test_roundtrip(self):
        escaped = envlauncher.DesktopEntryParser._escape_comments(self.unescaped)
        unescaped = envlauncher.DesktopEntryParser._unescape_comments(escaped)
        self.assertEqual(unescaped, self.unescaped)


class TestDesktopEntryParserFormatting(unittest.TestCase):
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

        parser = envlauncher.DesktopEntryParser.from_string(desktop_entry)
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

        parser = envlauncher.DesktopEntryParser.from_string(desktop_entry)
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

        parser = envlauncher.DesktopEntryParser.from_string(desktop_entry)
        export = parser.export_string()
        self.assertEqual(export, desktop_entry)


class TestDesktopEntryParserConfiguration(unittest.TestCase):
    def test_rcfile(self):
        desktop_entry = textwrap.dedent("""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --preferences
            Type=Application

            [X-EnvLauncher Preferences]
            Rcfile=~/.bashrc
        """).lstrip()
        config = envlauncher.DesktopEntryParser.from_string(desktop_entry)

        self.assertEqual(config.rcfile, '~/.bashrc')

        config.rcfile = '.venvrc'
        self.assertEqual(config.rcfile, '.venvrc')

        config.rcfile = 1234  # <- Bogus value.
        self.assertEqual(config.rcfile, '')  # <- Empty string.

    def test_banner(self):
        desktop_entry = textwrap.dedent("""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --preferences
            Type=Application

            [X-EnvLauncher Preferences]
            Banner=color
        """).lstrip()
        config = envlauncher.DesktopEntryParser.from_string(desktop_entry)

        self.assertEqual(config.banner, 'color')

        config.banner = 'plain'
        self.assertEqual(config.banner, 'plain')

        config.banner = 'none'
        self.assertEqual(config.banner, 'none')

        config.banner = 1234  # <- Bogus value.
        self.assertEqual(config.banner, 'color')  # <- Defaults to color.

    def test_get_actions(self):
        desktop_entry = textwrap.dedent("""
            [Desktop Entry]
            Name=EnvLauncher
            Exec=envlauncher --preferences
            Type=Application
            Actions=venv1;venv2;preferences;

            [Desktop Action venv1]
            Name=Python 3.9
            Exec=envlauncher --activate "~/.venv39/bin/activate" --directory "~/Projects/"

            [Desktop Action venv2]
            Name=Python 2.7
            Exec=envlauncher --activate "~/.venv27/bin/activate" --directory "~/Projects/legacy/"

            [Desktop Action preferences]
            Name=Preferences
            Exec=envlauncher --preferences
        """).lstrip()
        config = envlauncher.DesktopEntryParser.from_string(desktop_entry)

        actual = config.get_actions()
        expected = [
            ('Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
            ('Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
        ]
        self.assertEqual(actual, expected)

        # Check identifier/group mismatch (there's no "venv3" group).
        config._parser['Desktop Entry']['Actions'] = 'venv1;venv2;venv3;preferences;'
        actual = config.get_actions()
        expected = [
            ('Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
            ('Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
        ]
        self.assertEqual(actual, expected)

        # Action identifiers are reordered.
        config._parser['Desktop Entry']['Actions'] = 'venv2;venv1;preferences;'
        actual = config.get_actions()
        expected = [
            ('Python 2.7', '~/.venv27/bin/activate', '~/Projects/legacy/'),
            ('Python 3.9', '~/.venv39/bin/activate', '~/Projects/'),
        ]
        self.assertEqual(actual, expected)
