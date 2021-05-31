import os
import sys 
import subprocess

import numpy as np
import pandas as pd
# from epimargin.estimators import analytical_MPVS
# from epimargin.etl.commons import download_data
# from epimargin.etl.covid19india import (data_path, get_time_series,
#                                         load_all_data, state_code_lookup)
# from epimargin.smoothing import notched_smoothing
from flask import Flask, request
from google.cloud import storage

app = Flask(__name__)

# common parameters
## estimation
CI = 0.95
window = 7
gamma = 0.1 
infectious_period = 1/gamma
# smooth = notched_smoothing(window)

simulation_start = pd.Timestamp("April 15, 2021")
survey_date = "October 23, 2020"
num_sims = 1000
coalesce_states = ["Delhi", "Manipur", "Dadra And Nagar Haveli And Daman And Diu", "Andaman And Nicobar Islands"]

experiment_tag = "all_india_coalesced"


# cloud parameters
bucket_name = "vax-allocation"

# download common files at container start


# @app.route("/setup", methods = ["POST"])
# def setup():
#     pass 

@app.route("/epi", methods = ["POST"])
def epi():
    request_data = request.get_json()
    state_code = request_data["state_code"]
    district   = request_data["district"]
    print(f"received epi request for {state_code} - {district}")
    return "OK!"

@app.route("/tev", methods = ["POST"])
def tev():
    request_data = request.get_json()
    state_code = request_data["state_code"]
    district   = request_data["district"]
    print(f"received tev request for {state_code} - ${district}")
    return "OK!"

if __name__ == "__main__":
    app.run(
        debug = True, 
        host  = "0.0.0.0", 
        port  = int(os.environ.get("PORT", 8080))
    )
