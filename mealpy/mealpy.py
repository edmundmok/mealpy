import getpass
import json
import time
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from shutil import copyfile

import click
import requests
import strictyaml
import xdg

BASE_DOMAIN = 'secure.mealpal.com'
BASE_URL = f'https://{BASE_DOMAIN}'
LOGIN_URL = f'{BASE_URL}/1/login'
CITIES_URL = f'{BASE_URL}/1/functions/getCitiesWithNeighborhoods'
MENU_URL = f'{BASE_URL}/api/v1/cities/{{}}/product_offerings/lunch/menu'
RESERVATION_URL = f'{BASE_URL}/api/v2/reservations'
KITCHEN_URL = f'{BASE_URL}/1/functions/checkKitchen3'

HEADERS = {
    'Host': BASE_DOMAIN,
    'Origin': BASE_URL,
    'Referer': f'{BASE_URL}/login',
    'Content-Type': 'application/json',
}

KEYRING_SERVICENAME = BASE_DOMAIN

CONFIG_FILENAME = 'config.yaml'
COOKIES_FILENAME = 'cookies.txt'
ROOT_DIR = Path(__file__).resolve().parent.parent


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


class MealPal:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def login(self, user, password):
        data = {
            'username': user,
            'password': password,
        }
        request = self.session.post(LOGIN_URL, data=json.dumps(data))

        request.raise_for_status()

        return request.status_code

    def get_cities(self):
        request = self.session.post(CITIES_URL)
        request.raise_for_status()
        return request.json()['result']

    def get_city(self, city_name):
        city = next((i for i in self.get_cities() if i['name'] == city_name), None)
        return city

    def get_schedules(self, city_name):
        city_id = self.get_city(city_name)['objectId']
        request = self.session.get(MENU_URL.format(city_id))
        request.raise_for_status()
        return request.json()['schedules']

    def get_schedule_by_restaurant_name(self, restaurant_name, city_name):
        restaurant = next(
            i
            for i in self.get_schedules(city_name)
            if i['restaurant']['name'] == restaurant_name
        )
        return restaurant

    def get_schedule_by_meal_name(self, meal_name, city_name):
        return next(i for i in self.get_schedules(city_name) if i['meal']['name'] == meal_name)

    def reserve_meal(
            self,
            timing,
            city_name,
            restaurant_name=None,
            meal_name=None,
            cancel_current_meal=False,
    ):  # pylint: disable=too-many-arguments
        assert restaurant_name or meal_name
        if cancel_current_meal:
            self.cancel_current_meal()

        if meal_name:
            schedule_id = self.get_schedule_by_meal_name(meal_name, city_name)['id']
        else:
            schedule_id = self.get_schedule_by_restaurant_name(restaurant_name, city_name)['id']

        reserve_data = {
            'quantity': 1,
            'schedule_id': schedule_id,
            'pickup_time': timing,
            'source': 'Web',
        }

        request = self.session.post(RESERVATION_URL, json=reserve_data)
        return request.status_code

    def get_current_meal(self):
        request = self.session.post(KITCHEN_URL)
        return request.json()

    def cancel_current_meal(self):
        raise NotImplementedError()


def get_mealpal_credentials():
    config = load_config()
    email = config['email_address']
    password = getpass.getpass('Enter password: ')
    return email, password


def initialize_mealpal():
    cookies_path = xdg.XDG_CACHE_HOME / 'mealpy' / COOKIES_FILENAME
    mealpal = MealPal()
    mealpal.session.cookies = MozillaCookieJar()

    if cookies_path.exists():
        try:
            mealpal.session.cookies.load(cookies_path, ignore_expires=True, ignore_discard=True)
        except UnicodeDecodeError:
            pass
        else:
            # hacky way of validating cookies
            sleep_duration = 1
            for _ in range(5):
                try:
                    mealpal.get_schedules('San Francisco')
                except requests.HTTPError:
                    # Possible fluke, retry validation
                    print(f'Login using cookies failed, retrying after {sleep_duration} second(s).')
                    time.sleep(sleep_duration)
                    sleep_duration *= 2
                else:
                    print('Login using cookies successful!')
                    return mealpal

        print('Existing cookies are invalid, please re-enter your login credentials.')

    while True:
        email, password = get_mealpal_credentials()

        try:
            mealpal.login(email, password)
        except requests.HTTPError:
            print('Invalid login credentials, please try again!')
        else:
            break

    # save latest cookies
    print(f'Login successful! Saving cookies as {cookies_path}.')
    mealpal.session.cookies.save(cookies_path, ignore_discard=True, ignore_expires=True)

    return mealpal


def initialize_directories():
    """Mkdir all directories mealpy uses."""
    cache = Path(xdg.XDG_CACHE_HOME) / 'mealpy'
    config = Path(xdg.XDG_CONFIG_HOME) / 'mealpy'

    for i in (cache, config):
        i.mkdir(parents=True, exist_ok=True)


@click.group()
def cli():
    initialize_directories()


# SCHEDULER = BlockingScheduler()
# @SCHEDULER.scheduled_job('cron', hour=16, minute=59, second=58)
def execute_reserve_meal(restaurant, reservation_time, city):
    mealpal = initialize_mealpal()

    while True:
        try:
            status_code = mealpal.reserve_meal(
                reservation_time,
                restaurant_name=restaurant,
                city_name=city,
            )
            if status_code == 200:
                print('Reservation success!')
                # print('Leave this script running to reschedule again the next day!')
                break
            else:
                print('Reservation error, retrying!')
        except IndexError:
            print('Retrying...')
            time.sleep(0.05)

# SCHEDULER.start()


@cli.command('reserve', short_help='Reserve a meal on MealPal.')
@click.argument('restaurant')
@click.argument('reservation_time')
@click.argument('city')
def reserve(restaurant, reservation_time, city):
    execute_reserve_meal(restaurant, reservation_time, city)


if __name__ == '__main__':
    cli()
