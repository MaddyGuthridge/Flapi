"""
# Flapi > Main

A simple program to run Flapi commands
"""
import click
from click_default_group import DefaultGroup  # type: ignore
from .cli import install, repl, uninstall
from .cli.port_host import port_host_cmd
from .cli.diag import diag
from ._consts import VERSION


@click.group(cls=DefaultGroup, default='repl', default_if_no_args=True)
@click.version_option(".".join(str(n) for n in VERSION))
def cli():
    pass


cli.add_command(install)
cli.add_command(uninstall)
cli.add_command(repl)
cli.add_command(port_host_cmd, name="port-host")
cli.add_command(diag, name="diag")


if __name__ == '__main__':
    cli(auto_envvar_prefix="FLAPI")
