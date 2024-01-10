"""
# Flapi > Main

A simple program to run Flapi commands
"""
import click
from click_default_group import DefaultGroup  # type: ignore
from .cli import install_main, repl_main, uninstall_main
from .cli import consts
from pathlib import Path
from typing import Optional


@click.group(cls=DefaultGroup, default='repl', default_if_no_args=True)
@click.version_option(package_name='flapi')
def cli():
    pass


@cli.command()
@click.option(
    "-d",
    "--data-dir",
    default=consts.DEFAULT_IL_DATA_DIR,
    type=Path,
    prompt=True,
    help="The location of the Image-Line data directory"
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Always overwrite the server installation"
)
def install(data_dir: Path, force: bool):
    """Install the Flapi server to FL Studio"""
    install_main(data_dir, force)


@cli.command()
@click.option(
    "-d",
    "--data-dir",
    default=consts.DEFAULT_IL_DATA_DIR,
    type=Path,
    prompt=True,
    help="The location of the Image-Line data directory"
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Proceed with uninstallation without confirmation"
)
def uninstall(data_dir: Path, yes: bool):
    """Uninstall the Flapi server from FL Studio"""
    uninstall_main(data_dir, yes)


@cli.command()
@click.option(
    '-s',
    '--shell',
    type=click.Choice(["ipython", "python", "server"], case_sensitive=False),
    help="The shell to use with Flapi.",
    default=None,
)
def repl(shell: Optional[str]):
    """Launch a Python REPL connected to FL Studio"""
    repl_main(shell)


if __name__ == '__main__':
    cli()
