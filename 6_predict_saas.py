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
    pip install lxml
    pip install croniter
'''

# import libraries
import datetime
import os
import pickle
import nltk
import re
import scipy
import pytz
import json
import requests
import croniter
import time
import subprocess
import datetime as dt
import pandas as pd
from numpy import int32
from scipy import sparse
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from utils import get_weather
from utils import text_processing
from flask import Flask, jsonify, request


app = Flask(__name__)


def get_alert_predict():
    # Load the JSON data from the file
    with open("data/results/predict.json", "r") as file:
        predict = json.load(file)

    return predict


def get_last_predict_time():
    ti_m = os.path.getmtime("data/results/predict.json")
    m_ti = time.ctime(ti_m)
    t_obj = time.strptime(m_ti)
    T_stamp = time.strftime("%Y-%m-%d %H:%M:%S", t_obj)

    return T_stamp


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
def alarm_predict_endpoint():

    last_prediction_time = get_last_predict_time()
    predict = get_alert_predict()

    result = {
        "last_prediction_time": last_prediction_time,
        "regions_forecast": predict,
    }

    return result

