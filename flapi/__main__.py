"""
# Flapi > Main

A simple program to run Flapi commands
"""
from argparse import ArgumentParser
from .install import install as install_main
from pathlib import Path

cli = ArgumentParser(
    description='CLI tool for the Flapi library',
)
subparsers = cli.add_subparsers(dest="subcommand")


def subcommand(args=[], parent=subparsers):
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


@subcommand([argument(
    "-d",
    "--data-dir",
    type=Path,
    help="The location of the Image-Line data directory"
)])
def install(args):
    install_main(args.data_dir)


def main():
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)


if __name__ == '__main__':
    main()
