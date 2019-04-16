import getpass
import json
import pickle
import time
from os import path
from shutil import copyfile

import click
import requests
import strictyaml

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
COOKIES_FILENAME = 'cookies.pickle'


def load_config_from_file(file_path, schema):
    with open(file_path) as config_file:
        return strictyaml.load(config_file.read(), schema).data


def load_config():
    schema = strictyaml.Map({
        'email_address': strictyaml.Email(),
        'use_keyring': strictyaml.Bool(),
    })
    root_dir = path.abspath(path.dirname(__file__))
    template_config_path = path.join(root_dir, 'config.template.yaml')
    config_path = path.join(root_dir, CONFIG_FILENAME)

    # Create config file if it doesn't already exist
    if not path.isfile(config_path):
        copyfile(template_config_path, config_path)
        print(f'{CONFIG_FILENAME} has been created in your current directory.')
        print(f'Please update the email_address field in {CONFIG_FILENAME} with your email address for MealPal.')
        exit(1)

    config = load_config_from_file(template_config_path, schema)
    config.update(load_config_from_file(config_path, schema))
    return config


class MealPal:

    def __init__(self):
        self.cookies = None

    def login(self, user, password):
        data = {
            'username': user,
            'password': password,
        }
        request = requests.post(LOGIN_URL, data=json.dumps(data), headers=HEADERS)
        self.cookies = request.cookies
        return request.status_code

    @staticmethod
    def get_cities():
        request = requests.post(CITIES_URL, headers=HEADERS)
        return request.json()['result']

    def get_city(self, city_name):
        city = next((i for i in self.get_cities() if i['name'] == city_name), None)
        return city

    def get_schedules(self, city_name):
        city_id = self.get_city(city_name)['objectId']
        request = requests.get(MENU_URL.format(city_id), headers=HEADERS, cookies=self.cookies)
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

        request = requests.post(RESERVATION_URL, data=json.dumps(reserve_data), headers=HEADERS, cookies=self.cookies)
        return request.status_code

    def get_current_meal(self):
        request = requests.post(KITCHEN_URL, headers=HEADERS, cookies=self.cookies)
        return request.json()

    def cancel_current_meal(self):
        raise NotImplementedError()


def get_mealpal_credentials():
    config = load_config()
    email = config['email_address']
    password = getpass.getpass('Enter password: ')
    return email, password


def initialize_mealpal():
    root_dir = path.abspath(path.dirname(__file__))
    cookies_path = path.join(root_dir, COOKIES_FILENAME)
    mealpal = MealPal()

    if path.isfile(cookies_path):
        with open(cookies_path, 'rb') as cookies_file:
            mealpal.cookies = pickle.load(cookies_file)

        # hacky way of validating cookies
        sleep_duration = 1
        for _ in range(5):
            try:
                mealpal.get_schedules('San Francisco')
            except Exception:  # pylint: disable=broad-except
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
        if mealpal.login(email, password) == 200:
            break
        print('Invalid login credentials, please try again!')

    # save latest cookies
    print(f'Login successful! Saving cookies as {COOKIES_FILENAME}.')
    with open(cookies_path, 'wb') as cookies_file:
        pickle.dump(mealpal.cookies, cookies_file)

    return mealpal


@click.group()
def cli():
    pass


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
