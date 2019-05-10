import json
from collections import namedtuple
from unittest import mock

import pytest
import requests
import responses
from freezegun import freeze_time

from mealpy import config
from mealpy import mealpy

City = namedtuple('City', 'name objectId')


@pytest.fixture(autouse=True)
def mock_responses():
    with responses.RequestsMock() as _responses:
        yield _responses


class TestCity:

    @staticmethod
    def test_get_cities(mock_responses):
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

        cities = mealpy.MealPal.get_cities()
        city = [i for i in cities if i['name'] == 'San Francisco'][0]

        assert city.items() >= {
            'id': 'mock_id1',
            'state': 'CA',
            'name': 'San Francisco',
        }.items()

    @staticmethod
    def test_get_cities_bad_response(mock_responses):
        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.CITIES_URL,
            status=400,
        )

        with pytest.raises(requests.exceptions.HTTPError):
            mealpy.MealPal.get_cities()


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


class TestSchedule:

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
        schedule = mealpy.MealPal.get_schedule_by_restaurant_name('RestaurantName', mock_city.name)

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
    @pytest.mark.xfail(
        raises=StopIteration,
        reason='#24 Invalid restaurant input not handled',
    )
    def test_get_schedule_by_restaurant_name_not_found(mock_city):
        mealpy.MealPal.get_schedule_by_restaurant_name('NotFound', mock_city.name)

    @staticmethod
    @pytest.mark.usefixtures('mock_get_city', 'menu_url_response')
    @pytest.mark.xfail(
        raises=StopIteration,
        reason='#24 Invalid meal name not handled',
    )
    def test_get_schedule_by_meal_name_not_found(mock_city):
        mealpy.MealPal.get_schedule_by_meal_name('NotFound', mock_city.name)

    @staticmethod
    @pytest.mark.usefixtures('mock_get_city', 'menu_url_response')
    def test_get_schedule_by_meal_name(mock_city):
        schedule = mealpy.MealPal.get_schedule_by_meal_name('Spam and Eggs', mock_city.name)

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

        with pytest.raises(requests.HTTPError):
            mealpy.MealPal.get_schedules(mock_city.name)


class TestCurrentMeal:

    @staticmethod
    @pytest.fixture
    def current_meal():
        yield {
            'id': 'GUID',
            'createdAt': '2019-03-20T02:53:28.908Z',
            'date': 'March 20, 2019',
            'pickupTime': '12:30-12:45',
            'pickupTimeIso': ['12:30', '12:45'],
            'googleCalendarLink': (
                'https://www.google.com/calendar/render?action=TEMPLATE&text=Pick Up Lunch from MealPal&'
                'details=Pick up lunch from MealPal: MEALNAME from RESTAURANTNAME\nPickup instructions: BLAHBLAH&'
                'location=ADDRESS, CITY, STATE&dates=20190320T193000Z/20190320T194500Z&sf=true&output=xml'
            ),
            'mealpalNow': False,
            'orderNumber': '1111',
            'emojiWord': None,
            'emojiCharacter': None,
            'emojiUrl': None,
            'meal': {
                'id': 'GUID',
                'image': 'https://example.com/image.jpg',
                'description': 'spam, eggs, and bacon. Served on avocado toast. With no toast.',
                'name': 'Spam Eggs',
            },
            'restaurant': {
                'id': 'GUID',
                'name': 'RESTURANTNAME',
                'address': 'ADDRESS',
                'city': {
                    '__type': 'Object',
                    'className': 'cities',
                    'createdAt': '2016-06-22T14:33:23.000Z',
                    'latitude': '111.111',
                    'longitude': '-111.111',
                    'name': 'San Francisco',
                    'city_code': 'SFO',
                    'objectId': 'GUID',
                    'state': 'CA',
                    'timezone': -7,
                    'updatedAt': '2019-03-18T16:08:22.577Z',
                },
                'latitude': '111.1111',
                'longitude': '-111.1111',
                'lunchOpen': '11:30am',
                'lunchClose': '2:30pm',
                'pickupInstructions': 'BLAH BLAH',
                'state': 'CA',
                'timezoneOffset': -7,
                'neighborhood': {
                    'id': 'GUID',
                    'name': 'SoMa',
                },
            },
            'schedule': {
                '__type': 'Object',
                'objectId': 'GUID',
                'className': 'schedules',
                'date': {
                    '__type': 'Date',
                    'iso': '2019-03-20T00:00:00.000Z',
                },
            },
        }

    @staticmethod
    @pytest.fixture
    def success_response_no_reservation():
        yield {
            'result': {
                'status': 'OPEN',
                'kitchenMode': 'classic',
                'time': '19:59',
                'reserveUntil': '2019-03-20T10:30:00-07:00',
                'cancelUntil': '2019-03-20T15:00:00-07:00',
                'kitchenTimes': {
                    'openTime': '5pm',
                    'openTimeMilitary': 1700,
                    'openHourMilitary': 17,
                    'openMinutesMilitary': 0,
                    'openHour': '5',
                    'openMinutes': '00',
                    'openPeriod': 'pm',
                    'closeTime': '10:30am',
                    'closeTimeMilitary': 1030,
                    'closeHourMilitary': 10,
                    'closeMinutesMilitary': 30,
                    'closeHour': '10',
                    'closeMinutes': '30',
                    'closePeriod': 'am',
                    'lateCancelHour': 15,
                    'lateCancelMinutes': 0,
                },
                'today': {
                    '__type': 'Date',
                    'iso': '2019-03-20T02:59:42.000Z',
                },
            },
        }

    @staticmethod
    @pytest.fixture
    def kitchen_url_response(mock_responses, success_response_no_reservation):
        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.KITCHEN_URL,
            status=200,
            json=success_response_no_reservation,
        )

        yield mock_responses

    @staticmethod
    @pytest.fixture
    def kitchen_url_response_with_reservation(mock_responses, success_response_no_reservation, current_meal):
        success_response_no_reservation['reservation'] = current_meal

        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.KITCHEN_URL,
            status=200,
            json=success_response_no_reservation,
        )

        yield mock_responses

    @staticmethod
    @pytest.mark.usefixtures('kitchen_url_response')
    def test_get_current_meal_no_meal():
        mealpal = mealpy.MealPal()

        current_meal = mealpal.get_current_meal()

        assert 'reservation' not in current_meal

    @staticmethod
    @pytest.mark.usefixtures('kitchen_url_response_with_reservation')
    def test_get_current_meal():
        mealpal = mealpy.MealPal()

        current_meal = mealpal.get_current_meal()

        assert current_meal['reservation'].keys() >= {
            'id',
            'pickupTime',
            'orderNumber',
            'meal',
            'restaurant',
            'schedule',
        }

    @staticmethod
    @pytest.mark.xfail(raises=NotImplementedError)
    def test_cancel_current_meal():
        mealpal = mealpy.MealPal()
        mealpal.cancel_current_meal()


class TestReserve:

    @staticmethod
    @pytest.fixture()
    def reserve_response(mock_responses):  # pragma: no cover
        # Current unused
        response = {
            'result': {
                'date': 'March 20, 2019',
                'user_id': 'GUID',
                'google_calendar_link': (
                    'https://www.google.com/calendar/render?'
                    'action=TEMPLATE&'
                    'text=Pick Up Lunch from MealPal&'
                    'details=Pick up lunch from MealPal: BLAH BLAH BLAH&'
                    'location=LOCATION&'
                    'dates=20190320T194500Z/20190320T200000Z&'
                    'sf=true&'
                    'output=xml'
                ),
                'encoded_google_calendar_link': 'URI_ENCODED',
                'schedule': {
                    'schedule_id': 'GUID',
                    'ordered_quantity': 1,
                    'late_canceled_quantity': 0,
                    'pickup_window_start': '2019-03-20T12:45:00-07:00',
                    'pickup_window_end': '2019-03-20T13:00:00-07:00',
                    'google_calendar_link': 'LOL_WHAT_THIS_IS_DUPLICATE',
                    'encoded_google_calendar_link': 'ENCODED_URI',
                    'order_number': '1111',
                    'mealpal_now': False,
                    'emoji_word': None,
                    'emoji_character': None,
                    'emoji_url': None,
                    'reserve_until': '2019-03-20T10:30:00-07:00',
                    'cancel_until': '2019-03-20T15:00:00-07:00',
                    'meal': {
                        'name': 'MEAL_NAME',
                        'image_url': 'https://example.com/image.jpg',
                        'ingredients': 'INGREDIENT_DESCRIPTION',
                    },
                    'restaurant': {
                        'lunch_open_at': '2019-03-20T11:30:00-07:00',
                        'lunch_close_at': '2019-03-20T14:30:00-07:00',
                        'name': 'RESTAURANT_NAME',
                        'address': 'ADDRESS',
                        'latitude': '111.111',
                        'longitude': '-111.111',
                        'pickup_strategy': 'qr_codes',
                        'pickup_strategy_set': 'online',
                        'pickup_instructions': 'INSTRUCTIONS',
                        'city_name': 'San Francisco',
                        'city_state': 'CA',
                    },
                },
            },
        }

        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.KITCHEN_URL,
            status=200,
            json=response,
        )
        yield mock_responses

    @staticmethod
    @pytest.fixture()
    def reserve_response_failed(mock_responses):  # pragma: no cover
        # Current unused
        response = {'error': 'ERROR_RESERVATION_LIMIT'}
        mock_responses.add(
            responses.RequestsMock.POST,
            mealpy.KITCHEN_URL,
            status=400,
            json=response,
        )
        yield mock_responses

    @staticmethod
    def test_reserve_meal_by_meal_name():
        mealpal = mealpy.MealPal()

        schedule_id = 1
        timing = 'mock_timing'
        with mock.patch.object(
                mealpy.MealPal,
                'get_schedule_by_meal_name',
                return_value={'id': schedule_id},
        ) as mock_get_schedule_by_meal, \
                mock.patch.object(mealpal, 'session') as mock_requests:
            mealpal.reserve_meal(
                timing,
                'mock_city',
                meal_name='meal_name',
            )

        assert mock_get_schedule_by_meal.called
        assert mock_requests.post.called_with(
            mealpy.RESERVATION_URL,
            {
                'quantity': 1,
                'schedule_id': schedule_id,
                'pickup_time': timing,
                'source': 'Web',
            },
        )

    @staticmethod
    def test_reserve_meal_by_restaurant_name():
        mealpal = mealpy.MealPal()

        schedule_id = 1
        timing = 'mock_timing'
        with mock.patch.object(
                mealpy.MealPal,
                'get_schedule_by_restaurant_name',
                return_value={'id': schedule_id},
        ) as mock_get_schedule_by_restaurant, \
                mock.patch.object(mealpal, 'session') as mock_requests:
            mealpal.reserve_meal(
                timing,
                'mock_city',
                restaurant_name='restaurant_name',
            )

        assert mock_get_schedule_by_restaurant.called
        assert mock_requests.post.called_with(
            mealpy.RESERVATION_URL,
            {
                'quantity': 1,
                'schedule_id': schedule_id,
                'pickup_time': timing,
                'source': 'Web',
            },
        )

    @staticmethod
    def test_reserve_meal_missing_params():
        """Need to set restaurant_name or meal_name."""
        mealpal = mealpy.MealPal()
        with pytest.raises(AssertionError):
            mealpal.reserve_meal(mock.sentinel.timing, mock.sentinel.city)

    @staticmethod
    @pytest.mark.xfail(raises=NotImplementedError)
    def test_reserve_meal_cancel_meal():
        """Test that meal can be canceled before reserving.

        This test is a little redundant atm. But it'll probably make more sense if cancellation is moved to an cli arg.
        At least this gives test coverage.
        """
        mealpal = mealpy.MealPal()

        mealpal.reserve_meal(
            'mock_timing',
            'mock_city',
            restaurant_name='restaurant_name',
            cancel_current_meal=True,
        )


class TestCli:

    @staticmethod
    @pytest.fixture(autouse=True)
    @pytest.mark.usefixtures('mock_fs')
    def setup_fakefs(mock_fs):
        """Setup up fake filesystem structure."""
        config.initialize_directories()

    @staticmethod
    @pytest.fixture(autouse=True)
    def pinned_time():
        """Time pinned to the test data.

        This makes tests deterministic.
        """
        with freeze_time('2019-05-09 20:00') as frozen_time:
            yield frozen_time

    @staticmethod
    @pytest.fixture
    def cities_json(mock_fs):
        contents = json.dumps({
            'run_date': '2019-05-09T20:00:00.000000-00:00',
            'result': [
                {'id': 'UID', 'name': 'San Francisco'},
            ],
        })

        mock_fs.create_file(
            config.CACHE_DIR / 'cities.json',
            contents=contents,
        )

    @staticmethod
    @pytest.fixture
    def mock_get_cities():
        with mock.patch.object(
                mealpy.MealPal,
                'get_cities',
                return_value=[
                    {
                        'name': 'city1',
                    },
                    {
                        'name': 'city2',
                    },
                ],
        ) as _mock:
            yield _mock

    @staticmethod
    @pytest.mark.usefixtures('mock_get_cities')
    def test_list_ciites_not_cached():
        result = mealpy.list_cities()

        assert result == ['city1', 'city2']
        assert (config.CACHE_DIR / 'cities.json').exists()

    @staticmethod
    @pytest.mark.usefixtures('cities_json')
    def test_list_ciites_use_cache(mock_get_cities):
        result = mealpy.list_cities()

        assert result == ['San Francisco']
        assert not mock_get_cities.called, 'Should not be called if using cache.'

    @staticmethod
    @pytest.mark.usefixtures('cities_json')
    def test_list_cities_cache_invalidated(pinned_time, mock_get_cities):
        next_day = '2019-05-10T20:00:00.000000-00:00'
        pinned_time.move_to(next_day)

        # import pdb;pdb.set_trace()
        result = mealpy.list_cities()

        assert result == ['city1', 'city2']
        assert mock_get_cities.called, "Cache should be ignored because it's stale."
