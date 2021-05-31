import os
from flask import Flask, request

import pandas as pd
from .epi import * 
from .tev import * 

experiment_tag = "epi-step"
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

# cloud parameters
bucket_name = f"vax-allocation/{experiment_tag}"

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
