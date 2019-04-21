from collections import namedtuple

import pytest
import requests
import responses

from mealpy import mealpy

City = namedtuple('City', 'name objectId')


@pytest.fixture(autouse=True)
def mock_responses():
    with responses.RequestsMock() as _responses:
        yield _responses


class TestGetCity:

    @staticmethod
    def test_get_city(mock_responses):
        response = {
            'result': [
                {
                    'id': 'mock_id1',
                    'objectId': 'mock_objectId1',
                    'state': 'CA',
                    'name': 'San Francisco',
                    'city_code': 'SFO',
                    'latitude': 'mock_latitude',
                    'longitude': 'mock_longitude',
                    'timezone': -7,
                    'countryCode': 'usa',
                    'countryCodeAlphaTwo': 'us',
                    'defaultLocale': 'en-US',
                    'dinner': False,
                    'neighborhoods': [
                        {
                            'id': 'mock_fidi_id',
                            'name': 'Financial District',
                        },
                        {
                            'id': 'mock_soma_id',
                            'name': 'SoMa',
                        },
                    ],
                },
                {
                    'id': 'mock_id2',
                    'objectId': 'mock_objectId2',
                    'state': 'WA',
                    'name': 'Seattle',
                    'city_code': 'SEA',
                    'latitude': 'mock_latitude',
                    'longitude': 'mock_longitude',
                    'timezone': -7,
                    'countryCode': 'usa',
                    'countryCodeAlphaTwo': 'us',
                    'defaultLocale': 'en-US',
                    'dinner': False,
                    'neighborhoods': [
                        {
                            'id': 'mock_belltown_id',
                            'name': 'Belltown',
                        },
                    ],
                },
            ],
        }

        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.CITIES_URL,
            json=response,
        )

        mealpal = mealpy.MealPal()
        city = mealpal.get_city('San Francisco')

        assert city.items() >= {
            'id': 'mock_id1',
            'state': 'CA',
            'name': 'San Francisco',
        }.items()

    @staticmethod
    def test_get_city_not_found(mock_responses):
        response = {
            'result': [
                {
                    'id': 'mock_id1',
                    'objectId': 'mock_objectId1',
                    'state': 'CA',
                    'name': 'San Francisco',
                    'city_code': 'SFO',
                },
            ],
        }

        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.CITIES_URL,
            json=response,
        )

        mealpal = mealpy.MealPal()
        city = mealpal.get_city('Not San Francisco')

        assert not city

    @staticmethod
    def test_get_city_bad_response(mock_responses):
        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.CITIES_URL,
            status=400,
        )

        mealpal = mealpy.MealPal()
        with pytest.raises(requests.exceptions.HTTPError):
            mealpal.get_city('Not San Francisco')


class TestLogin:

    @staticmethod
    def test_login(mock_responses):
        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.LOGIN_URL,
            status=200,
            json={
                'id': 'GUID',
                'email': 'email',
                'status': 3,
                'firstName': 'first_name',
                'lastName': 'last_name',
                'sessionToken': 'r:GUID',
                'city': {
                    'id': 'GUID',
                    'name': 'San Francisco',
                    'city_code': 'SFO',
                    'countryCode': 'usa',
                    '__type': 'Pointer',
                    'className': 'City',
                    'objectId': 'GUID',
                },
            },
        )

        mealpal = mealpy.MealPal()

        assert mealpal.login('username', 'password') == 200

    @staticmethod
    def test_login_fail(mock_responses):
        mock_responses.add(
            method=responses.RequestsMock.POST,
            url=mealpy.LOGIN_URL,
            status=404,
            json={
                'code': 101,
                'error': 'An error occurred while blah blah, try agian.',
            },
        )

        mealpal = mealpy.MealPal()

        with pytest.raises(requests.HTTPError):
            mealpal.login('username', 'password')


class TestGetSchedule:

    @staticmethod
    @pytest.fixture
    def mock_city():
        yield City('mock_city', 'mock_city_object_id')

    @staticmethod
    @pytest.fixture
    def success_response():
        """A complete response example for MENU_URL endpoint."""
        yield {
            'city': {
                'id': 'GUID',
                'name': 'San Francisco',
                'state': 'CA',
                'time_zone_name': 'America/Los_Angeles',
            },
            'generated_at': '2019-04-01T00:00:00Z',
            'schedules': [{
                'id': 'GUID',
                'priority': 9,
                'is_featured': True,
                'date': '20190401',
                'meal': {
                    'id': 'GUID',
                    'name': 'Spam and Eggs',
                    'description': 'Soemthign sometlhing python',
                    'cuisine': 'asian',
                    'image': 'https://example.com/image.jpg',
                    'portion': 2,
                    'veg': False,
                },
                'restaurant': {
                    'id': 'GUID',
                    'name': 'RestaurantName',
                    'address': 'RestaurantAddress',
                    'state': 'CA',
                    'latitude': '111.111',
                    'longitude': '-111.111',
                    'neighborhood': {
                        'name': 'Financial District',
                        'id': 'GUID',
                    },
                    'city': {
                        'name': 'San Francisco',
                        'id': 'GUID',
                        'timezone_offset_hours': -7,
                    },
                    'open': '2019-04-01T00:00:00Z',
                    'close': '2019-04-01T00:00:00Z',
                    'mpn_open': '2019-04-01T00:00:00Z',
                    'mpn_close': '2019-04-01T00:00:00Z',
                },
            }],
        }

    @staticmethod
    @pytest.fixture
    def menu_url_response(mock_responses, success_response, mock_city):
        mock_responses.add(
            responses.RequestsMock.GET,
            mealpy.MENU_URL.format(mock_city.objectId),
            status=200,
            json=success_response,
        )

        yield mock_responses

    @staticmethod
    @pytest.fixture
    def mock_get_city(mock_responses, mock_city):
        mock_responses.add(
            method=responses.RequestsMock.POST,
            url=mealpy.CITIES_URL,
            json={
                'result': [{
                    'id': 'mock_id1',
                    'objectId': mock_city.objectId,
                    'name': mock_city.name,
                }],
            },
        )
        yield

    @staticmethod
    @pytest.mark.usefixtures('mock_get_city', 'menu_url_response')
    def test_get_schedule_by_restaurant_name(mock_city):
        mealpal = mealpy.MealPal()

        schedule = mealpal.get_schedule_by_restaurant_name('RestaurantName', mock_city.name)

        meal = schedule['meal']
        restaurant = schedule['restaurant']

        assert meal.items() >= {
            'id': 'GUID',
            'name': 'Spam and Eggs',
        }.items()

        assert restaurant.items() >= {
            'id': 'GUID',
            'name': 'RestaurantName',
            'address': 'RestaurantAddress',
        }.items()

    @staticmethod
    @pytest.mark.usefixtures('mock_get_city', 'menu_url_response')
    def test_get_schedule_by_restaurant_name_not_found(mock_city):
        mealpal = mealpy.MealPal()

        # TODO(#24):  Handle invalid restaurant
        with pytest.raises(StopIteration):
            mealpal.get_schedule_by_restaurant_name('NotFound', mock_city.name)

    @staticmethod
    @pytest.mark.usefixtures('mock_get_city', 'menu_url_response')
    def test_get_schedule_by_meal_name_not_found(mock_city):
        mealpal = mealpy.MealPal()

        # TODO(#24):  Handle invalid restaurant
        with pytest.raises(StopIteration):
            mealpal.get_schedule_by_meal_name('NotFound', mock_city.name)

    @staticmethod
    @pytest.mark.usefixtures('mock_get_city', 'menu_url_response')
    def test_get_schedule_by_meal_name(mock_city):
        mealpal = mealpy.MealPal()

        schedule = mealpal.get_schedule_by_meal_name('Spam and Eggs', mock_city.name)

        meal = schedule['meal']
        restaurant = schedule['restaurant']

        assert meal.items() >= {
            'id': 'GUID',
            'name': 'Spam and Eggs',
        }.items()

        assert restaurant.items() >= {
            'id': 'GUID',
            'name': 'RestaurantName',
            'address': 'RestaurantAddress',
        }.items()

    @staticmethod
    @pytest.mark.usefixtures('mock_get_city')
    def test_get_schedules_fail(mock_responses, mock_city):
        mock_responses.add(
            method=responses.RequestsMock.GET,
            url=mealpy.MENU_URL.format(mock_city.objectId),
            status=400,
        )

        mealpal = mealpy.MealPal()

        with pytest.raises(requests.HTTPError):
            mealpal.get_schedules(mock_city.name)
