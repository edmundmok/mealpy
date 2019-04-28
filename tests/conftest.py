import pytest
import xdg
from pyfakefs.fake_filesystem_unittest import Patcher

from mealpy import config


@pytest.fixture()
def mock_fs():
    """Mock filesystem calls with pyfakefs."""

    # Ordering matters for reloading modules. Patch upstream dependencies first, otherwise downstream dependencies will
    # "cache" before monkey-patching occurs. i.e. config uses xdg, xdg needs to be reloaded first
    modules_to_reload = [
        xdg,
        config,
    ]

    with Patcher(modules_to_reload=modules_to_reload) as patcher:
        yield patcher.fs
