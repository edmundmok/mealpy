from pathlib import Path

import pendulum
import pytest
import xdg
from pyfakefs.fake_filesystem_unittest import Patcher

import mealpy


@pytest.fixture()
def mock_fs():
    """Mock filesystem calls with pyfakefs."""

    # Ordering matters for reloading modules. Patch upstream dependencies first, otherwise downstream dependencies will
    # "cache" before monkey-patching occurs. i.e. config uses xdg, xdg needs to be reloaded first
    modules_to_reload = [
        xdg,
        mealpy.config,
        mealpy.mealpy,
    ]
    modules_to_ignore = [
        pendulum,
    ]

    # This allows installed packages to access the very files they installed.
    venv = Path('./venv').resolve()

    with Patcher(
            modules_to_reload=modules_to_reload,
            additional_skip_names=[i.__name__ for i in modules_to_ignore],
    ) as patcher:
        filesystem = patcher.fs
        filesystem.add_real_directory(venv)

        yield filesystem
