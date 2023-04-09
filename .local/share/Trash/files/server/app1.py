import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p><h1>KMA SaaS WS!</h1></p>"
