"""Tests for EnvLauncher."""
import contextlib
import io
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
