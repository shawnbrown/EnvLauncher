"""Tests for EnvLauncher."""
import contextlib
import io
import os
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


class TestXDGDirectoryFunctions(unittest.TestCase):
    def setUp(self):
        original_environ = os.environ.copy()
        os.environ.clear()
        self.addCleanup(os.environ.update, original_environ)
        self.addCleanup(os.environ.clear)

    def test_xdg_get_data_home(self):
        os.environ['XDG_DATA_HOME'] = '/other/location/share'
        os.environ['HOME'] = '/home/testuser'
        data_home = envlauncher.xdg_get_data_home()
        self.assertEqual(data_home, '/other/location/share')

    def test_xdg_get_data_home_default(self):
        os.environ['HOME'] = '/home/testuser'
        data_home = envlauncher.xdg_get_data_home()
        self.assertEqual(data_home, '/home/testuser/.local/share')

    def test_xdg_get_data_dirs(self):
        os.environ['XDG_DATA_DIRS'] = '/foo/bar:/var/lib/baz'
        data_home = envlauncher.xdg_get_data_dirs()
        self.assertEqual(data_home, ['/foo/bar', '/var/lib/baz'])

    def test_xdg_get_data_dirs_default(self):
        data_home = envlauncher.xdg_get_data_dirs()
        self.assertEqual(data_home, ['/usr/local/share', '/usr/share'])
