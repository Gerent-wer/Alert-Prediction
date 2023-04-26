import datetime

import pandas as pd
from dotenv import load_dotenv
import requests
import json
import os

load_dotenv()
API_KEY = os.getenv('WEATHER_API_TOKEN')
REGIONS_DICTIONARY_FILE = "data/0_raw_other_data/regions.csv"
OUTPUT_FOLDER = "data/1_weather_for_12_hours"

df_regions = pd.read_csv(REGIONS_DICTIONARY_FILE)

def get_json(region,today_date):
    level = "hours"
    country = "Ukraine"
    start_date = end_date = today_date

    city = df_regions[df_regions["region_alt"] == region]["center_city_en"].values[0]
    location = f"{city},{country}"

    file_name = f"weather_{city.lower()}_{start_date}_{end_date}.json"

    if not os.path.isfile(f"{OUTPUT_FOLDER}/{file_name}"):
        url_base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
        url_key = f"?key={API_KEY}"
        url_location = location
        url_start_data = start_date
        url_end_data = end_date
        url_level = level

        url = f"{url_base_url}/{url_location}/{url_start_data}/{url_end_data}/{url_key}&include=hours&unitGroup=metric&contentType=json"

        response = requests.request("GET", url)
        city_weather_json = response.json()

        with open(f"{OUTPUT_FOLDER}/{file_name}", 'w') as outfile:
            json.dump(city_weather_json, outfile)
            #outfile.write(city_weather_json)

    else:
        print(f"Weather data for the \nregion {region}; \nstart_date {start_date}; \nend_date {end_date}; \nis ready")


    with open(f"{OUTPUT_FOLDER}/{file_name}") as outfile:
        weather_json = json.load(outfile)

    hours_weather_json = []

    for day in weather_json['days']:
        for hour in day['hours']:
            hours_weather_json.append(hour)

    hours_df = pd.DataFrame(hours_weather_json)

    return weather_json


def get_next_date(date):
    return (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")


def get_df_weather(jsonData):
    # prepare wether data
    df_data_day = pd.DataFrame(jsonData['days'])
    df_data_day = df_data_day[df_data_day.columns[0:33]].add_prefix('day_')
    hours_forecast = jsonData['days'][0]['hours']
    df_weather_hours = pd.DataFrame(hours_forecast).add_prefix('hour_')
    df_weather_hours['hour_int'] = pd.to_datetime(df_weather_hours['hour_datetime']).dt.hour

    # merge date with hours
    df_weather_hours['key'] = 1
    df_data_day['key'] = 1
    df_weather_final = pd.merge(df_data_day, df_weather_hours, on='key')

    return df_weather_final


def get_weather_for_12_hours(city, date):
    jsonData = get_json(city, date)
    current_hour = int(date.strftime("%H"))

    # count needed hours
    weather_all_data_day1 = get_df_weather(jsonData)
    hours_needed = (weather_all_data_day1['hour_int'] >= current_hour) & (weather_all_data_day1['hour_int'] <= (current_hour + 12))
    weather_all_data_day1 = weather_all_data_day1[hours_needed]
    df_weather_final = weather_all_data_day1
    hours_left = 12 - weather_all_data_day1.shape[0]

    # get our from the next day
    if (hours_left > 0):
        jsonData = get_json(city, get_next_date(date))
        weather_all_data_day2 = get_df_weather(jsonData)
        hours_needed_2 = ((weather_all_data_day2['hour_int'] <= hours_left))
        weather_all_data_day2 = weather_all_data_day2[hours_needed_2]
        df_weather_final = pd.concat([weather_all_data_day1, weather_all_data_day2], axis=0)

    # merge data with regions
    df_weather_final['city'] = city
    df_final = pd.merge(df_weather_final, df_regions, left_on="city", right_on="center_city_en")

    return df_final

