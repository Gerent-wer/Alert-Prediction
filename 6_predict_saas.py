'''
    Libraries for installation
    pip install nltk
    pip install scipy
    pip install requests
    pip install pandas
    pip install scikit-learn
    pip install bs4
    pip install flask
    pip install python-dotenv
    pip install num2words

'''

# import libraries
import datetime
import pickle
import nltk
import re
import scipy
import pytz
import json
import requests
import datetime as dt
import pandas as pd
from scipy import sparse
from numpy import int32
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from utils import get_weather
from utils import text_processing
from flask import Flask, jsonify, request

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# you can get API keys for free here - https://www.weatherapi.com/
RSA_API_KEY = ""

app = Flask(__name__)


def generate_forecast():

    ### get and preprocess ISW files

    # get article from yesterday
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    yesterday_day = yesterday.day
    yesterday_month = yesterday.month
    yesterday_year = yesterday.year

    file = text_processing.get_article_from_yesterday(yesterday_day, yesterday_month, yesterday_year)
    data = text_processing.read_html(file)

    # articles preprocess
    def preprocess_all_text(data):
        pattern = "\[(\d+)\]"
        data['main_html_v1'] = data['main_html'].apply(lambda x: re.sub(pattern, "", str(x)))
        data['main_html_v2'] = data['main_html_v1'].apply(lambda x: re.sub(r'http(\S+.*\s)', "", x))
        data['main_html_v3'] = data['main_html_v2'].apply(lambda x: re.sub(r'2022|2023|©2022|©2023|\xa0|\n', "", x))
        data['main_html_v4'] = data['main_html_v3'].apply(lambda x: BeautifulSoup(x).text)
        data['main_html_v5'] = data['main_html_v4'].apply(lambda x: text_processing.remove_names_and_dates(x))

        return data


    data_preprocessed = preprocess_all_text(data)    # %%
    data_preprocessed = data_preprocessed.drop(['main_html_v1', 'main_html_v2', 'main_html_v3', 'main_html_v4'], axis=1)

    data_preprocessed['report_text_lemm'] = data_preprocessed['main_html_v5'].apply(
        lambda x: text_processing.preprocess(x, "lemm"))
    data_preprocessed['report_text_stemm'] = data_preprocessed['main_html_v5'].apply(
        lambda x: text_processing.preprocess(x, "stemm"))

    docs = data_preprocessed['report_text_lemm'].tolist()

    ### ISW vectorize

    cv = CountVectorizer()
    word_count_vector = cv.fit_transform(docs)
    tfidf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
    tfidf_transformer.fit(word_count_vector)
    tf_idf_vector = tfidf_transformer.transform(word_count_vector)
    feature_names = cv.get_feature_names_out()

    data_preprocessed['keywords'] = data_preprocessed['report_text_stemm'].apply(
        lambda x: text_processing.convert_doc_to_vector(x, feature_names, tf_idf_vector))

    #### Part of script: Final preprocessing

    data_preprocessed["date_datetime"] = pd.to_datetime(data_preprocessed["date"])
    data_preprocessed['date_tomorrow_datetime'] = data_preprocessed['date_datetime'].apply(
        lambda x: x + datetime.timedelta(days=1))
    data_preprocessed = data_preprocessed.rename(columns={"date_datetime": "report_date"})

    data_vectorised = tf_idf_vector.toarray()
    vectors_df = pd.DataFrame(data_vectorised)
    vectors_df['date'] = pd.to_datetime(today)

    df_isw_short = data_preprocessed[['date', 'report_text_lemm', 'keywords', 'date_tomorrow_datetime']]

    ### Predict

    tfidf = pickle.load(open("models/tfidf_transformer_v1.pkl", "rb"))
    cv = pickle.load(open("models/count_vectorizer_v1.pkl", "rb"))
    model = pickle.load(open("models/training_models/4_logreg_1.5f.pkl", "rb"))

    cities = ['Vinnytsia', 'Simferopol', 'Lutsk', 'Dnipro', 'Donetsk', 'Zhytomyr', 'Uzhgorod', 'Zaporozhye',
              'Ivano-Frankivsk', 'Kyiv',
              'Kropyvnytskyi', 'Luhansk', 'Lviv', 'Mykolaiv', 'Odesa', 'Poltava', 'Rivne', 'Sumy', 'Ternopil',
              'Kharkiv', 'Kherson',
              'Khmelnytskyi', 'Cherkasy', 'Chernivtsi', 'Chernihiv']

    date = datetime.datetime.now(pytz.timezone('Europe/Kyiv'))

    result = {}
    for city in cities:

        df_weather_final = get_weather.get_weather_for_12_hours(city, date)

        # merge
        df_weather_final['key'] = 1
        df_isw_short['key'] = 1
        df_all = df_weather_final.merge(df_isw_short, how='left', left_on='key', right_on='key')

        # drop
        to_drop = ['key', 'date', 'date_tomorrow_datetime', 'keywords', 'report_text_lemm']
        if 'sunrise' in df_all.columns:
            exceptions = ['sunset', 'sunrise']
            to_drop.extend(exceptions)
        df_weather_matrix_v1 = df_all.drop(to_drop, axis=1)

        # final dataset
        df_weather_matrix_v1['Unnamed: 0'] = 0
        df_weather_matrix_v1 = df_weather_matrix_v1[
            ['Unnamed: 0', 'day_datetimeEpoch', 'day_tempmax', 'day_tempmin', 'day_temp', 'day_dew', 'day_humidity',
             'day_precip', 'day_precipcover', 'day_solarradiation', 'day_solarenergy', 'day_uvindex', 'day_moonphase',
             'hour_datetimeEpoch', 'hour_temp', 'hour_humidity', 'hour_dew', 'hour_precipprob', 'hour_snow',
             'hour_snowdepth', 'hour_windgust', 'hour_windspeed', 'hour_winddir', 'hour_pressure', 'hour_visibility',
             'hour_cloudcover', 'hour_severerisk', 'region_id']]

        cv_vector_model = cv.transform(df_all['report_text_lemm'].values.astype('U'))
        TF_IDF_MODEL = tfidf.transform(cv_vector_model)

        df_weather_matrix_v1_csr = scipy.sparse.csr_matrix(df_weather_matrix_v1)
        df_all_data_csr = scipy.sparse.hstack((df_weather_matrix_v1_csr, TF_IDF_MODEL), format='csr')

        # predict
        predicted = model.predict(df_all_data_csr)
        predicted_int = predicted.tolist()
        
        current_time = pd.Timestamp.now()
        hours = []

        for i in range(12):
            hour = date + datetime.timedelta(hours=i)
            hour_rounded = hour.replace(minute=0, second=0, microsecond=0)
            hours.append(hour_rounded.strftime('%Y-%m-%d %H:%M'))

        result[city] = dict(zip(hours, predicted_int))

    #json_data = json.dumps(result, indent=1)

    return result

    # ###     Save result
    # result = pd.DataFrame(result)
    # VERSION = "2"
    # result.to_csv(f'data/results/results_{VERSION}.txt', sep='\t', index=False)







    # url_base_url = "http://api.weatherapi.com"
    # url_api = "v1"
    # url_endpoint = ""
    # url_key = f"?key={RSA_API_KEY}"
    # url_location = ""
    # url_data = ""
    # url_aqi = ""
    # url_lang = ""
    # date_datatime = datetime.strptime(data, "%Y-%m-%d")  # перетворюємо строку в datatime
    # now = datetime.now()
    #
    # # обираэмо потрібний нам метод API в залежності від дати
    # if date_datatime.date() == now.date():
    #     url_endpoint = "current.json"
    # elif date_datatime.date() < now.date():
    #     url_endpoint = "history.json"
    # else:
    #     url_endpoint = "future.json"
    #
    # # Записуємо отримані параметри, якщо вони є
    # if location:
    #     url_location = f"&q={location}"
    #
    # if data:
    #     url_data = f"&dt={data}"
    #
    # if aqi:
    #     url_aqi = f"&aqi={aqi}"
    #
    # if lang:
    #     url_lang = f"&lang={lang}"
    #
    # url = f"{url_base_url}/{url_api}/{url_endpoint}{url_key}{url_location}{url_data}{url_aqi}{url_lang}"
    #
    # payload = {}
    # headers = {}
    #
    # response = requests.request("GET", url, headers=headers, data=payload)
    # return json.loads(response.text)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Alarm Predict Project. Send a POST request for this link (/api/v1/alertprediction/generate) with param: regions_forecast = city</h2></p>"


@app.route(
    "/api/v1/alertprediction/generate",
    methods=["POST"],
)
def weather_endpoint():
    start_dt = dt.datetime.now()
    # json_data = request.get_json()
    #
    # name = ""
    # if json_data.get("requester_name"):
    #     name = json_data.get("requester_name")

    weather = generate_forecast()
    end_dt = dt.datetime.now()

    result = {
        "event_start_datetime": start_dt.isoformat(),
        "event_finished_datetime": end_dt.isoformat(),
        "event_duration": str(end_dt - start_dt),
        "weather": weather,
    }

    return result
