import pytest
import xdg
from pyfakefs.fake_filesystem_unittest import Patcher

from mealpy import config


@pytest.fixture()
def mock_fs():
    """ Fake filesystem. """
    with Patcher(modules_to_reload=[config, xdg]) as patcher:
        yield patcher.fs
