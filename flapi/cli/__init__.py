"""
# Flapi > CLI

Code for running the Flapi CLI
"""
from .install import install_main
from .uninstall import uninstall_main
from .shell import shell_main


__all__ = [
    'install_main',
    'uninstall_main',
    'shell_main',
]
