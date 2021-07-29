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


class XDGDirectoryBases(unittest.TestCase):
    def test_data_home(self):
        xdgdir = envlauncher.XDGDirectory({
            'XDG_DATA_HOME': '/other/location/share',
            'HOME': '/home/testuser',
        })
        self.assertEqual(xdgdir.data_home, '/other/location/share')

    def test_data_home_default(self):
        xdgdir = envlauncher.XDGDirectory({
            'HOME': '/home/testuser',
        })
        self.assertEqual(xdgdir.data_home, '/home/testuser/.local/share')

    def test_data_dirs(self):
        xdgdir = envlauncher.XDGDirectory({
            'HOME': '/home/testuser',
            'XDG_DATA_DIRS': '/foo/bar:/var/lib/baz',
        })
        self.assertEqual(xdgdir.data_dirs, ['/foo/bar', '/var/lib/baz'])

    def test_data_dirs_default(self):
        xdgdir = envlauncher.XDGDirectory({
            'HOME': '/home/testuser',
        })
        self.assertEqual(xdgdir.data_dirs, ['/usr/local/share', '/usr/share'])


class XDGDirectoryFindFirstFilepath(unittest.TestCase):
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

        # Create an XDGDirectory instance with a custom environ.
        cls.xdgdir = envlauncher.XDGDirectory({
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
        filepath = self.xdgdir.find_first_filepath('applications', 'app1.desktop')
        regex = r'/highest/preference/applications/app1[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_middle_preference(self):
        filepath = self.xdgdir.find_first_filepath('applications', 'app2.desktop')
        regex = r'/middle/preference/applications/app2[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_lowest_preference(self):
        filepath = self.xdgdir.find_first_filepath('applications', 'app3.desktop')
        regex = r'/lowest/preference/applications/app3[.]desktop$'
        self.assertRegex(filepath, regex)

    def test_no_matching_file(self):
        with self.assertRaises(FileNotFoundError):
            self.xdgdir.find_first_filepath('applications', 'app4.desktop')


class XDGDirectoryMakeHomeFilepath(unittest.TestCase):
    def test_home_filepath(self):
        xdgdir = envlauncher.XDGDirectory({
            'XDG_DATA_HOME': os.path.join('/base/directory'),
        })
        filepath = xdgdir.make_home_filepath('applications', 'app1.desktop')
        expected = '/base/directory/applications/app1.desktop'
        self.assertEqual(filepath, expected)


class TestXDGDesktop(unittest.TestCase):
    def setUp(self):
        self.desktop = envlauncher.XDGDesktop()

    @staticmethod
    def textformat(text):  # <- Helper method.
        """Format string for ConfigParser compatibility."""
        return f'{textwrap.dedent(text).strip()}\n\n'

    def test_unchanged(self):
        """Check that parser exports values as they are given."""
        minimal_example = self.textformat("""
            [Desktop Entry]
            Type=Application
            Name=Hello World
            Exec=gnome-terminal -- bash -c "echo Hello World;bash"
        """)

        self.desktop.read_string(minimal_example)
        export = self.desktop.export_string()
        self.assertEqual(export, minimal_example, msg='should match original')

    def test_preserve_comments(self):
        """Comments should be preserved, too."""
        minimal_example = self.textformat("""
            [Desktop Entry]
            Type=Application
            Name=Hello World
            Exec=gnome-terminal -- bash -c "echo Hello World;bash"
            #Keywords=hello;world; <- A COMMENT!
        """)

        self.desktop.read_string(minimal_example)
        export = self.desktop.export_string()
        self.assertEqual(export, minimal_example)
