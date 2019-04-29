# mealpy

[![Build Status](https://travis-ci.org/edmundmok/mealpy.svg?branch=master)](https://travis-ci.org/edmundmok/mealpy)
[![Coveralls github](https://img.shields.io/coveralls/github/edmundmok/mealpy.svg)](https://img.shields.io/coveralls/github/edmundmok/mealpy?branch=master)
![license](https://img.shields.io/github/license/edmundmok/mealpy.svg)

Reserve your meals on MealPal automatically, as soon as the kitchen opens.
Never miss your favourite MealPal meals again!

## Description

*[MealPal](https://www.mealpal.com) offers lunch and dinner subscriptions giving you access to the best restaurants
for less than $6 per meal.*

This script automates the ordering process by allowing you to specify your desired restaurant and pickup timing in
advance. Just run the script before the MealPal kitchen opens at 5pm to get your order, and beat the competition to
getting the meals from popular restaurants!

## Installation

Install virtualenv with all required dependencies and activate it:

```bash
make venv
source venv/bin/activate
```

## Quickstart

```bash
python -m mealpy --help
```

### Reserve a meal

```bash
# python -m mealpy.py reserve RESTAURANT RESERVATION_TIME CITY
python -m mealpy reserve "Coast Poke Counter - Battery St." "12:15pm-12:30pm" "San Francisco"
```

## Files

### Configuration

Upon the first run, a config will be created in $XDG_CONFIG_HOME (~/.config/mealpy) from the [template](config.template.yaml).
You'll can override the default values.

### Cookies

This script stores cookies created from initial login.
This is how the script can rerun without re-asking every time.
This can be found in $XDG_CACHE_HOME (~/.cache/mealpy).
