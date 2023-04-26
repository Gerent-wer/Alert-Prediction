import datetime

import pandas as pd
#from dotenv import load_dotenv
import requests
import json
import os

#oad_dotenv()
API_KEY = "9TS2B3LDPRU8UYW7QBPLEUV6S"
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
        #city_weather_json = weather.get_weather(location, start_date, end_date, level)
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


# import urllib.request
# import sys
# import datetime
# import json
# import pytz
# import os
# import scipy
# import pandas as pd

# from utils import text_processing

# API_KEY = "9TS2B3LDPRU8UYW7QBPLEUV6S"

# DIR_REGIONS = 'data/0_raw_other_data/regions.csv'
# SAVED_FORCASTS = 'data/1_weather_for_12_hours'

# df_regions = pd.read_csv(DIR_REGIONS)


# def save_file(data, city, date):
#     data_object = json.dumps(data)

#     # open file for writing, "w"
#     f = open(f"{SAVED_FORCASTS}/{city}_{date}.json", "w")

#     # write json object to file
#     f.write(data_object)

#     # close file
#     f.close()


# def read_file(path):
#     f = open(path)

#     # returns JSON object as
#     # a dictionary
#     data = json.load(f)

#     # Closing file
#     f.close()
#     return data


# def get_weather(city, date):
#     path = f"{SAVED_FORCASTS}/{city}_{date}.json"
#     if (os.path.exists(path)):
#         jsonData = read_file(path)
#         return jsonData
#     location = f"{city},Ukraine"
#     url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}?key={API_KEY}&include=hours&unitGroup=metric&contentType=json'
#     try:
# #         with urllib.request.urlopen(url) as response:
# #             jsonData = json.loads(response.read().decode())

#         ResultBytes = urllib.request.urlopen(url)
        
#         # Parse the results as JSON
#         jsonData = json.load(ResultBytes)


#     except urllib.error.HTTPError as e:
#         ErrorInfo = e.read().decode()
#         print('Error code: ', e.code, ErrorInfo)
#         sys.exit()
#     except  urllib.error.URLError as e:
#         ErrorInfo = e.read().decode()
#         print('Error code: ', e.code, ErrorInfo)
#         sys.exit()
#     text_processing.save_file(jsonData, city, date)
#     return jsonData


# def get_next_date(date):
#     return (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")


def get_df_weather(jsonData):
    df_data_day = pd.DataFrame(jsonData['days'])
    df_data_day = df_data_day[df_data_day.columns[0:33]].add_prefix('day_')
    hours_forecast = jsonData['days'][0]['hours']
    df_weather_hours = pd.DataFrame(hours_forecast).add_prefix('hour_')
    df_weather_hours['hour_int'] = pd.to_datetime(df_weather_hours['hour_datetime']).dt.hour
    df_weather_hours['key'] = 1
    df_data_day['key'] = 1
    df_weather_final = pd.merge(df_data_day, df_weather_hours, on='key')
    return df_weather_final


def get_weather_for_12_hours(city, date):
    jsonData = get_json(city, date)
    current_hour = int(date.strftime("%H"))
    weather_all_data_day1 = get_df_weather(jsonData)
    hours_needed = (weather_all_data_day1['hour_int'] >= current_hour) & (
                weather_all_data_day1['hour_int'] <= (current_hour + 12))
    weather_all_data_day1 = weather_all_data_day1[hours_needed]
    df_weather_final = weather_all_data_day1
    hours_left = 12 - weather_all_data_day1.shape[0]
    if (hours_left > 0):
        jsonData = get_weather(city, get_next_date(date))
        weather_all_data_day2 = get_df_weather(jsonData)
        hours_needed_2 = ((weather_all_data_day2['hour_int'] <= hours_left))
        weather_all_data_day2 = weather_all_data_day2[hours_needed_2]
        df_weather_final = pd.concat([weather_all_data_day1, weather_all_data_day2], axis=0)
    df_weather_final['city'] = city
    df_final = pd.merge(df_weather_final, df_regions, left_on="city", right_on="center_city_en")

    return df_final

