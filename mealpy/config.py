from pathlib import Path
from shutil import copyfile

import strictyaml
import xdg

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILENAME = 'config.yaml'


def initialize_directories():  # pragma: no cover
    """Mkdir all directories mealpy uses."""
    cache = Path(xdg.XDG_CACHE_HOME) / 'mealpy'
    config = Path(xdg.XDG_CONFIG_HOME) / 'mealpy'

    for i in (cache, config):
        i.mkdir(parents=True, exist_ok=True)


def load_config_from_file(config_file: Path, schema: strictyaml.Map):
    return strictyaml.load(config_file.read_text(), schema).data


def load_config():
    schema = strictyaml.Map({
        'email_address': strictyaml.Email(),
        'use_keyring': strictyaml.Bool(),
    })

    template_config_path = ROOT_DIR / 'config.template.yaml'

    config_path = xdg.XDG_CONFIG_HOME / 'mealpy' / CONFIG_FILENAME

    # Create config file if it doesn't already exist
    if not config_path.exists():
        copyfile(str(template_config_path), str(config_path))
        exit(
            f'{config_path} has been created.\n'
            f'Please update the email_address field in {config_path} with your email address for MealPal.',
        )

    config = load_config_from_file(template_config_path, schema)
    config.update(load_config_from_file(config_path, schema))
    return config
