import pandas as pd
#from dotenv import load_dotenv
import requests
import json
import os


def get_weather_for_12_hours(region,today_date):

    #oad_dotenv()
    API_KEY = "9TS2B3LDPRU8UYW7QBPLEUV6S"
    REGIONS_DICTIONARY_FILE = "data/0_raw_other_data/regions.csv"
    OUTPUT_FOLDER = "data/1_weather_for_12_hours"



    df_regions = pd.read_csv(REGIONS_DICTIONARY_FILE)
    df_regions.head(10)


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

        url = f"{url_base_url}/{url_location}/{url_start_data}/{url_end_data}/{url_key}"

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

    return hours_df