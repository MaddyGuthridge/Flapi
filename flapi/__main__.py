"""
# Flapi > Main

A simple program to run Flapi commands
"""
from argparse import ArgumentParser
from .cli import install_main, repl_main, uninstall_main
from pathlib import Path
from typing import Any

cli = ArgumentParser(
    description='CLI tool for the Flapi library',
)
subparsers = cli.add_subparsers(dest="subcommand")


def subcommand(*args: Any, parent=subparsers):
    """
    A neat little decorator for reducing my immense confusion when dealing with
    the Argparse library

    Source: https://mike.depalatis.net/blog/simplifying-argparse.html
    """
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator


def argument(*name_or_flags, **kwargs):
    """
    Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return (list(name_or_flags), kwargs)


@subcommand(
    argument(
        "-d",
        "--data-dir",
        type=Path,
        help="The location of the Image-Line data directory"
    ),
    argument(
        "-f",
        "--force",
        action='store_true',
        help="Always overwrite the server installation"
    ),
)
def install(args):
    """Install the Flapi server to FL Studio"""
    install_main(args.data_dir, args.force)


@subcommand(
    argument(
        "-d",
        "--data-dir",
        type=Path,
        help="The location of the Image-Line data directory"
    ),
    argument(
        "-y",
        "--yes",
        action='store_true',
        help="Proceed with uninstallation without confirmation"
    ),
)
def uninstall(args):
    """Uninstall the Flapi server from FL Studio"""
    uninstall_main(args.data_dir, args.yes)


@subcommand(
    argument(
        "-s",
        "--shell",
        type=str,
        help="The shell to use with Flapi. Either 'ipython' or 'python'.",
        default=None,
    ),
)
def repl(args):
    """Launch a Python REPL connected to FL Studio"""
    repl_main(args.shell)


cli.set_defaults(subcommand='repl')


def main():
    args = cli.parse_args()
    if args.subcommand is None:
        repl_main()
    else:
        args.func(args)


if __name__ == '__main__':
    main()
