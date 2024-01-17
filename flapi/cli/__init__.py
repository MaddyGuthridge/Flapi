"""
# Flapi > CLI

Code for running the Flapi CLI
"""
from .install import install
from .uninstall import uninstall
from .repl import repl


__all__ = [
    'install',
    'uninstall',
    'repl',
]
