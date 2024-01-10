"""
# Flapi > CLI

Code for running the Flapi CLI
"""
from .install import install_main
from .uninstall import uninstall_main
from .repl import repl_main


__all__ = [
    'install_main',
    'uninstall_main',
    'repl_main',
]
