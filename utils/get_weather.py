import urllib.request
import sys
import datetime
import json
import pytz
import os
import scipy
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('WEATHER_API_TOKEN')

DIR_REGIONS = "../data/0_raw_other_data/regions.csv"
SAVED_FORCASTS = "../data/1_weather_for_12_hours"

df_regions = pd.read_csv(DIR_REGIONS)

def save_file(data,city, date):
    data_object = json.dumps(data)

    # open file for writing, "w"
    f = open(f"{SAVED_FORCASTS}/{city}_{date}.json","w")

    # write json object to file
    f.write(data_object)

    # close file
    f.close()


def read_file(path):
    f = open(path)

    # returns JSON object as
    # a dictionary
    data = json.load(f)


    # Closing file
    f.close()
    return data


def get_weather(city, date):
    path = f"{SAVED_FORCASTS}/{city}_{date}.json"
    if (os.path.exists(path)):
        jsonData = read_file(path)
        return jsonData
    location = f"{city},Ukraine"
    url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}?key={API_KEY}&include=hours&unitGroup=metric&contentType=json'
    try:
      ResultBytes = urllib.request.urlopen(url)

      # Parse the results as JSON
      jsonData = json.load(ResultBytes)

    except urllib.error.HTTPError  as e:
      ErrorInfo= e.read().decode()
      print('Error code: ', e.code, ErrorInfo)
      sys.exit()
    except  urllib.error.URLError as e:
      ErrorInfo= e.read().decode()
      print('Error code: ', e.code,ErrorInfo)
      sys.exit()
    save_file(jsonData,city, date)
    return jsonData


def get_next_date(date):
    return (date+datetime.timedelta(days=1)).strftime("%Y-%m-%d")


def get_df_weather(jsonData):
    df_data_day = pd.DataFrame(jsonData['days'])
    df_data_day = df_data_day[df_data_day.columns[0:33]].add_prefix('day_')
    hours_forecast=jsonData['days'][0]['hours']
    df_weather_hours = pd.DataFrame(hours_forecast).add_prefix('hour_')
    df_weather_hours['hour_int']=pd.to_datetime(df_weather_hours['hour_datetime']).dt.hour
    df_weather_hours['key'] = 1
    df_data_day['key'] = 1
    df_weather_final = pd.merge(df_data_day,df_weather_hours, on='key')
    return df_weather_final


def get_weather_for_12_hours(city,date):
    jsonData = get_weather(city, date.strftime("%Y-%m-%d"))
    current_hour = int(date.strftime("%H"))
    weather_all_data_day1 = get_df_weather(jsonData)
    hours_needed = (weather_all_data_day1['hour_int']>=current_hour)&(weather_all_data_day1['hour_int']<=(current_hour+12))
    weather_all_data_day1=weather_all_data_day1[hours_needed]
    df_weather_final = weather_all_data_day1
    hours_left=12-weather_all_data_day1.shape[0]
    if(hours_left>0):
        jsonData = get_weather(city, get_next_date(date))
        weather_all_data_day2 = get_df_weather(jsonData)
        hours_needed_2 = ((weather_all_data_day2['hour_int']<=hours_left))
        weather_all_data_day2=weather_all_data_day2[hours_needed_2]
        df_weather_final = pd.concat([weather_all_data_day1, weather_all_data_day2], axis=0)
    df_weather_final['city']=city
    df_final = pd.merge(df_weather_final,df_regions,left_on="city",right_on="center_city_en")


    return df_final
