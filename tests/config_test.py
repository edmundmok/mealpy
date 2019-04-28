from unittest import mock

import pytest

from mealpy import config


@pytest.fixture
def mock_config_template(mock_fs):
    template_config_path = config.ROOT_DIR / 'config.template.yaml'
    mock_fs.create_file(template_config_path, contents='test')
    yield template_config_path


@pytest.mark.usefixtures('mock_fs')
def test_get_config_config_not_exist(mock_config_template):
    with pytest.raises(SystemExit), \
            mock.patch.object(config, 'copyfileobj') as copyfileobj:
        config.get_config()

    assert copyfileobj.called, 'Template should be copied to user config.'
