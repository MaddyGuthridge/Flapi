"""
# Flapi > CLI > Consts

Constants used by the Flapi CLI
"""
import os
from pathlib import Path


DEFAULT_IL_DATA_DIR = Path(os.path.expanduser("~/Documents/Image-Line"))
"""
The default location of the Image-Line data directory
"""


CONNECTION_TIMEOUT = 60.0
"""
The maximum duration to wait for a connection with FL Studio
"""
