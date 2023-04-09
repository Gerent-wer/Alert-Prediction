import datetime as dt
import json
import requests

API_KEY = "9TS2B3LDPRU8UYW7QBPLEUV6S"

def get_weather(location: str, start_data: str, end_data: str, level: str):
    url_base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    url_key = f"?key={API_KEY}"
    url_location = {location}
    url_start_data = {start_data}
    url_end_data = {end_data}
    url_level = {level}

    url = f"{url_base_url}/{url_location}/{url_start_data}/{url_end_data}/{url_key}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    json_data = response.json()

    print(response)
    print(json_data)

    return json.load(response)