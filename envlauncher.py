#!/usr/bin/env python
import subprocess
import tempfile


def launch_environment(script, directory):
    """Launch a gnome-terminal and activate an development environment."""
    rcfile_lines = [
        f'source {script}',
        f'cd {directory}' if directory else '',
    ]

    with tempfile.NamedTemporaryFile(mode='w+') as fh:
        fh.write('\n'.join(rcfile_lines))
        fh.seek(0)

        args = ['gnome-terminal', '--', 'bash', '--rcfile', fh.name]
        process = subprocess.Popen(args)
        process.wait(10)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('script', help='Path to the environment activation script.')
    parser.add_argument('--dir', help='Working directory.')

    args = parser.parse_args()
    launch_environment(args.script, args.dir)
