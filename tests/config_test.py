from textwrap import dedent
from unittest import mock

import pytest

from mealpy import config


@pytest.fixture(autouse=True)
def mock_config_template(mock_fs):
    """Fixture to bypass pyfakefs and use real template file from repo."""
    template_config_path = config.ROOT_DIR / 'config.template.yaml'
    mock_fs.add_real_file(template_config_path)
    yield template_config_path


@pytest.fixture
def mock_config(mock_fs):
    """Fixture to generate a user config file."""
    config_path = config.CONFIG_DIR / 'config.yaml'

    mock_fs.create_file(
        config_path,
        contents=dedent('''\
            ---
            email_address: 'test@test.com'
            use_keyring: False
        '''),
    )
    yield config_path


def test_get_config_config_not_exist(mock_config_template, mock_fs):
    """Test that config template is copied over to user config."""
    with pytest.raises(SystemExit), \
            mock.patch.object(config, 'copyfileobj') as copyfileobj:
        config.get_config()

    assert copyfileobj.called, 'Template should be copied to user config.'


def test_get_config_override(mock_config_template, mock_config, mock_fs):
    """Test that user config values override default values."""
    _config = config.get_config()

    assert _config['email_address'] == 'test@test.com'


@pytest.mark.xfail(
    raises=config.strictyaml.YAMLValidationError,
    reason='User config values are not optionally merged with default, #23',
)
def test_get_config_missing_values(mock_config_template, mock_config, mock_fs):  # pragma: no cover
    """Test that config will default to values from template if user did not override."""
    mock_config.write_text(dedent('''\
        ---
        email_address: 'test@test.com'
    '''))

    _config = config.get_config()

    assert _config['email_address'] == 'test@test.com', 'email_address should come from user config override.'
    assert not _config['use_keyring'], 'use_keyring should be default value from template.'
