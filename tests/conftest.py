import sys
from pathlib import Path
import shutil
import pytest

SRC_PATH = Path(__file__).resolve().parents[1] / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture
def test_data_dir():
    """Provides a consistent test directory that can be pre-authorized."""
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    yield test_dir
    # Clean up after each test
    if test_dir.exists():
        shutil.rmtree(test_dir)
        test_dir.mkdir(exist_ok=True)
