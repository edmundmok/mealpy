from functools import lru_cache
from pathlib import Path
from shutil import copyfileobj

import strictyaml
import xdg

ROOT_DIR = Path(__file__).resolve().parent.parent


def initialize_directories():  # pragma: no cover
    """Mkdir all directories mealpy uses."""
    cache = xdg.XDG_CACHE_HOME / 'mealpy'
    config = xdg.XDG_CONFIG_HOME / 'mealpy'

    for i in (cache, config):
        i.mkdir(parents=True, exist_ok=True)


def load_config_from_file(config_file: Path):  # pragma: no cover
    schema = strictyaml.Map({
        'email_address': strictyaml.Email(),
        'use_keyring': strictyaml.Bool(),
    })

    return strictyaml.load(config_file.read_text(), schema).data


@lru_cache(maxsize=1)
def get_config():
    initialize_directories()

    template_config_path = ROOT_DIR / 'config.template.yaml'
    assert template_config_path.exists()

    config_path = xdg.XDG_CONFIG_HOME / 'mealpy' / 'config.yaml'

    # Create config file if it doesn't already exist
    if not config_path.exists():  # pragma: no cover
        copyfileobj(template_config_path.open(), config_path.open('w'))
        exit(
            f'{config_path} has been created.\n'
            f'Please update the email_address field in {config_path} with your email address for MealPal.',
        )

    config = load_config_from_file(template_config_path)
    config.update(load_config_from_file(config_path))
    return config
