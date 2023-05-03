# import libraries
import os
import json
import time
from flask import Flask, jsonify


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
