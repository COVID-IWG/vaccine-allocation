import os

import pandas as pd
from flask import Flask, request

from commons import initial_conditions
from epi import run_simulation, epi_columns
from tev import run_evaluation, tev_columns
from agg import run_aggregation

experiment_tag = "main"
app = Flask(__name__)


@app.route("/epi", methods = ["POST"])
def epi():
    request_data = request.get_json()
    state_code   = request_data["state_code"]
    district     = request_data["district"]
    print(f"received epi request for {state_code} - {district}")
    district_initial_conditions = initial_conditions[epi_columns].loc[state_code, district]
    run_simulation(state_code, district, district_initial_conditions, experiment_tag)
    return "OK!"

@app.route("/tev", methods = ["POST"])
def tev():
    request_data = request.get_json()
    state_code   = request_data["state_code"]
    district     = request_data["district"]
    print(f"received tev request for {state_code} - {district}")
    district_population = initial_conditions[tev_columns].loc[state_code, district]
    run_evaluation(state_code, district, district_population, experiment_tag)
    return "OK!"

@app.route("/agg", methods = ["POST"])
def agg():
    request_data = request.get_json()
    if "state_code" in request_data:
        state_code = request_data["state_code"]
        print(f"received agg request for {state_code}")
    else:
        print(f"received agg request for all states")
        state_code = None
    run_aggregation(state_code, experiment_tag)
    return "OK!"

@app.route("/viz", methods = ["POST"])
def viz():
    request_data = request.get_json()
    if "state_code" in request_data:
        state_code = request_data["state_code"]
    else: 
        state_code = None

    if "district" in request_data:
        district = request_data["district"]
    else: 
        district = None

    print(f"received viz request for {state_code} - {district}")
    return "OK!"

if __name__ == "__main__":
    app.run(
        debug = True, 
        host  = "0.0.0.0", 
        port  = int(os.environ.get("PORT", 8080))
    )
