import getpass
import json
import time
from http.cookiejar import MozillaCookieJar

import click
import pendulum
import requests
import xdg

from mealpy import config


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

COOKIES_FILENAME = 'cookies.txt'
CACHE_HOME = xdg.XDG_CACHE_HOME / 'mealpy'


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

    @staticmethod
    def get_cities():
        response = requests.post(CITIES_URL)
        response.raise_for_status()

        result = response.json()['result']

        return result

    @staticmethod
    def get_schedules(city_name):
        city_id = next((i['objectId'] for i in MealPal.get_cities() if i['name'] == city_name), None)
        request = requests.get(MENU_URL.format(city_id))
        request.raise_for_status()
        return request.json()['schedules']

    @staticmethod
    def get_schedule_by_restaurant_name(restaurant_name, city_name):
        restaurant = next(
            i
            for i in MealPal.get_schedules(city_name)
            if i['restaurant']['name'] == restaurant_name
        )
        return restaurant

    @staticmethod
    def get_schedule_by_meal_name(meal_name, city_name):
        return next(i for i in MealPal.get_schedules(city_name) if i['meal']['name'] == meal_name)

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
            schedule_id = MealPal.get_schedule_by_meal_name(meal_name, city_name)['id']
        else:
            schedule_id = MealPal.get_schedule_by_restaurant_name(restaurant_name, city_name)['id']

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
    email = config.get_config()['email_address']
    password = getpass.getpass('Enter password: ')
    return email, password


def initialize_mealpal():
    cookies_path = CACHE_HOME / COOKIES_FILENAME
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
                    MealPal.get_schedules('San Francisco')
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


@click.group()
def cli():  # pragma: no cover
    config.initialize_directories()


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
def reserve(restaurant, reservation_time, city):  # pragma: no cover
    execute_reserve_meal(restaurant, reservation_time, city)


@cli.group(name='list')
def cli_list():  # pragma: no cover
    pass


@cli_list.command('cities', short_help='List available cities.')
def cli_list_cities():  # pragma: no cover
    print('\n'.join(list_cities()))


def list_cities():
    cities_file = CACHE_HOME / 'cities.json'

    cities = []

    if cities_file.exists():
        cities_data = json.load(cities_file.open())
        cache_expire_date = pendulum.parse(cities_data['run_date']).add(hours=1)
        if pendulum.now() < cache_expire_date:
            cities = [i['name'] for i in cities_data['result']]

    if not cities:
        cities_data = MealPal.get_cities()
        json.dump({'run_date': str(pendulum.now()), 'result': cities_data}, cities_file.open('w'))

        cities = [i['name'] for i in cities_data]

    return cities


@cli_list.command('restaurants', short_help='List available restaurants.')
@click.argument('city')
def cli_list_restaurants(city):  # pragma: no cover
    restaurants = [i['restaurant']['name'] for i in MealPal.get_schedules(city)]
    print('\n'.join(restaurants))


@cli_list.command('meals', short_help='List meal choices.')
@click.argument('city')
def cli_list_meals(city):  # pragma: no cover
    restaurants = [i['meal']['name'] for i in MealPal.get_schedules(city)]
    print('\n'.join(restaurants))
