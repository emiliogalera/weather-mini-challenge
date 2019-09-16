
# Request web content through api url
import urllib.request as request

# used to convert string to json
import json
from json import JSONDecodeError

# fix possible whitespace problem in strings
import re

# datetime module, used to get weekday from date string
import datetime

# deepcopy so it does not overwrite variables
from copy import deepcopy

# for mean calculation
import statistics

from typing import Any, Dict, List


BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?q="

WEEKDAY_LIST = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def url_builder(city: str, country: str, appid: str) -> str:
    """Builds the url for request of 5 day forecast from openweathermap.org"""
    if not isinstance(city, str):
        raise TypeError("City name must be a string!")
    if not isinstance(country, str):
        raise TypeError("Country must be a string!")
    if not isinstance(appid, str):
        raise TypeError("User Key must be an string")

    if " " == city[0] or " " == city[-1]:
        city = city.strip()
    if " " in country or len(country) != 2:
        raise ValueError("country must be a valid postal abbreviation")

    city = re.sub('\s+', '+', city)
    country = country.lower()

    return f"{BASE_URL}{city},{country}&APPID={appid}"

def json_data_fetsher(url: str) -> Dict[str, Any]:
    """Gets data from url and transfoms it to json, if possible"""
    try:
        page = request.urlopen(url)
    except request.HTTPError as error:
        raise request.HTTPError(url, error.code, "Not a Valid URL!", error.hdrs, error.fp)

    try:
        page_string = page.read()
        json_data = json.loads(page_string)
        return json_data
    except JSONDecodeError:
        raise JSONDecodeError("Could not extract JSON data from page")

def weekday_data_transform(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform dt_txt of json data from string to {weekday: str, hour: str}"""
    try:
        json_data_ret = deepcopy(json_data)
        for item in json_data_ret["list"]:
            item['dt_txt'] = get_wd_and_hour(item['dt_txt'])
        return json_data_ret
    except KeyError:
        raise KeyError("Json object has no 'list' key. Check if URL is correct and if 5 day forecast in OpenWeather")

def get_wd_and_hour(dt_txt: str) -> Dict[str, str]:
    """Gets a string of <year>-<month>-<day> <hour>:<min>:<sec> and extracts the weekday"""
    dict_to_return = {}
    hour_str = dt_txt.split(" ")[1]
    date_list = [int(x) for x in dt_txt.split(" ")[0].split("-")]
    date = datetime.date(*date_list)

    return {'weekday': f'{WEEKDAY_LIST[date.weekday()]}',
            'hour': hour_str,
            'date': dt_txt.split(" ")[0]}

def get_humidity_by_weekday(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compress the information of humidity of an entire day as the mean value"""
    dict_to_return = {i: [] for i in WEEKDAY_LIST}

    for item in json_data['list']:
        dict_to_return[item['dt_txt']['weekday']].append(item['main']['humidity'])

    return dict_to_return

def generate_days_list(target_date: datetime.date) -> List[str]:
    """Generate a list of 5 days ahead of target_date"""
    timedelta = datetime.timedelta(days=1)
    ret_list = []
    for i in range(5):
        target_date += timedelta
        ret_list.append(WEEKDAY_LIST[target_date.weekday()])
    return ret_list


# Case for script run.
# It uses my own id for openweather
if __name__ == "__main__":
    # Parameters to build the url
    appid = "a9bb5d61d2f0cc2221f9b3280e620edf"
    country = "br"
    city = "Ribeirao Preto"

    url = url_builder(city, country, appid)
    jdata = json_data_fetsher(url)

    # This alrady tests the json data. If something went wrong the json data
    # does not have 'list' in it.
    jdata_by_weekday = weekday_data_transform(jdata)
    humidity_data = get_humidity_by_weekday(jdata_by_weekday)

    # days to use the umbrella
    umbrella_days = []

    # five days list from today
    today = datetime.datetime.today()
    five_days_list = generate_days_list(today)

    # days to use the umbrella
    umbrella_days = []
    for day in five_days_list:
        if statistics.mean(humidity_data[day]) >= 70.0 and len(umbrella_days) < 3:
            umbrella_days.append(day)

    if umbrella_days:
        message = "You should take an umbrella in these days: "
        if len(umbrella_days) > 1:
            for uday in umbrella_days[:-1]:
                message += f"{uday}, "
            message = message[:-2]
            message += f" and {umbrella_days[-1]}."
        else:
            message = f"You should take an umbrella only on {umbrella_days[0]}"
        print(message)
    else:
        print(f"No umbrella needed for the next five days! {city} is a hot and dry city!")

