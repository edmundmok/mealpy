import pytest
import responses

from mealpy import mealpy


@pytest.fixture(autouse=True)
def mock_responses():
    with responses.RequestsMock() as _responses:
        yield _responses


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
