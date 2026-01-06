import sys
import itertools
from pathlib import Path
import pytest

# Ensure the source code is in the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Polyfill for itertools.batched (Python < 3.12 compatibility)
# This is required because the Flapi project targets Python 3.12+, but the test environment
# might be running an older version (e.g. 3.9 in standard Linux distros).
if not hasattr(itertools, 'batched'):
    def batched(iterable, n):
        if n < 1:
            raise ValueError('n must be at least one')
        it = iter(iterable)
        while True:
            chunk = tuple(itertools.islice(it, n))
            if not chunk:
                break
            yield chunk
    itertools.batched = batched

@pytest.fixture
def random_bytes():
    """Factory to generate random bytes of a given length"""
    def _gen(length: int):
        # Use a fixed seed or simple generation for reproducibility if needed,
        # but for now pseudo-random is fine.
        return bytes(bytearray([x % 256 for x in range(length)]))
    return _gen
