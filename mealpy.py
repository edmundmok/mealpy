import getpass
import json
import requests
import time

BASE_DOMAIN = 'secure.mealpal.com'
BASE_URL = 'https://' + BASE_DOMAIN
LOGIN_URL = BASE_URL + '/1/login'
CITIES_URL = BASE_URL + '/1/functions/getCitiesWithNeighborhoods'
MENU_URL = BASE_URL + '/api/v1/cities/%s/product_offerings/lunch/menu'
RESERVATION_URL = BASE_URL + '/api/v2/reservations'
KITCHEN_URL = BASE_URL + '/1/functions/checkKitchen3'

LOGGED_IN_COOKIE = 'isLoggedIn'

HEADERS = {
    'Host': BASE_DOMAIN,
    'Origin': BASE_URL,
    'Referer': BASE_URL + '/login',
    'Content-Type': 'application/json',
}


class MealPal:

    def __init__(self):
        self.headers = HEADERS
        self.cookies = None
        self.cities = None
        self.schedules = None

    def login(self, username, password):
        data = {'username': username, 'password': password}
        r = requests.post(
            LOGIN_URL, data=json.dumps(data), headers=self.headers)
        self.cookies = r.cookies
        self.cookies.set(LOGGED_IN_COOKIE, 'true', domain=BASE_URL)

    def get_cities(self):
        if not self.cities:
            r = requests.post(CITIES_URL, headers=self.headers)
            self.cities = r.json()['result']
        return self.cities

    def get_city(self, city_name):
        if not self.cities:
            self.get_cities()
        return filter(lambda x: x['name'] == city_name, self.cities)[0]

    def get_schedules(self, city_name, city_id=None):
        if not city_id:
            city_id = self.get_city(city_name)['objectId']
        r = requests.get(
            MENU_URL % city_id, headers=self.headers, cookies=self.cookies)
        self.schedules = r.json()['schedules']
        return self.schedules

    def get_schedule_by_restaurant_name(
            self, restaurant_name, city_name=None, city_id=None):
        if not self.schedules:
            self.get_schedules(city_name, city_id)
        return filter(lambda x: x['restaurant']['name'] == restaurant_name,
                      self.schedules)[0]

    def get_schedule_by_meal_name(
            self, meal_name, city_name=None, city_id=None):
        if not self.schedules:
            self.get_schedules(city_name, city_id)
        return filter(lambda x: x['meal']['name'] == meal_name,
                      self.schedules)[0]

    def reserve_meal(
            self, timing, restaurant_name=None, meal_name=None, city_name=None,
            city_id=None, cancel_current_meal=False):
        assert restaurant_name or meal_name
        if cancel_current_meal:
            self.cancel_current_meal()

        if meal_name:
            schedule_id = self.get_schedule_by_meal_name(
                meal_name, city_name, city_id)['id']
        else:
            schedule_id = self.get_schedule_by_restaurant_name(
                restaurant_name, city_name, city_id)['id']

        reserve_data = {
            'quantity': 1,
            'schedule_id': schedule_id,
            'pickup_time': timing,
            'source': 'Web'
        }

        r = requests.post(
            RESERVATION_URL, data=json.dumps(reserve_data),
            headers=self.headers, cookies=self.cookies)
        return r

    def get_current_meal(self):
        r = requests.post(
            KITCHEN_URL, headers=self.headers, cookies=self.cookies)
        return r.json()

    def cancel_current_meal(self):
        pass

mp = MealPal()
print "Enter email: "
email = raw_input()
print "Enter password: "
password = getpass.getpass()
mp.login(email, password)
while (True):
    try:
        print mp.reserve_meal(
            '12:15pm-12:30pm', restaurant_name='Hive Coffee Bar',
            city_name='San Francisco')
    except IndexError:
        print "Retrying..."
        time.sleep(5)
