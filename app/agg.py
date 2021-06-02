import os
from itertools import chain, product

import numpy as np

from commons import bucket, natl_weights, phi_points, state_weights


def empty_dict():
    return {pt: np.array(0) for pt in chain([(25, "novax")], product([_ * 365 * 100 for _ in phi_points], ["random", "contact", "mortality"]))}

def run_aggregation(state_code, experiment_tag):
    if state_code:
        run_aggregation_state(state_code, experiment_tag)
    else:
        run_aggregation_natl(experiment_tag)

def run_aggregation_state(state_code, experiment_tag):
    deaths                = empty_dict()
    YLL                   = empty_dict()
    total_TEV             = empty_dict()
    total_VSLY            = empty_dict()
    state_per_capita_TEV  = empty_dict()
    state_per_capita_VSLY = empty_dict()
    natl_per_capita_TEV   = empty_dict()
    natl_per_capita_VSLY  = empty_dict()
    
    for blob in bucket.list_blobs(prefix = f"{experiment_tag}/tev/{state_code}"):
        if "decomposition" in blob.name:
            pass 
        else:
            *_, district, filename = blob.name.split("/")
            *_, phi, vax_policy    = filename.replace("phi", "").replace(".npz", "").split("_")
            phi = int(phi)

            sw = state_weights.loc[state_code, district]
            nw = natl_weights .loc[state_code, district]
            
            blob.download_to_filename(f"/tmp/{filename}")
            with np.load(f"/tmp/{filename}") as f:
                deaths[phi, vax_policy]                    = deaths[phi, vax_policy]                    + f["deaths"]
                YLL[phi, vax_policy]                       = YLL[phi, vax_policy]                       + f["YLL"]
                total_TEV.loc[phi, vax_policy]             = total_TEV.loc[phi, vax_policy]             + f["total_TEV"]
                total_VSLY.loc[phi, vax_policy]            = total_VSLY.loc[phi, vax_policy]            + f["total_VSLY"]
                state_per_capita_TEV.loc[phi, vax_policy]  = state_per_capita_TEV.loc[phi, vax_policy]  + f["per_capita_TEV"]  * sw
                state_per_capita_VSLY.loc[phi, vax_policy] = state_per_capita_VSLY.loc[phi, vax_policy] + f["per_capita_VSLY"] * sw
                natl_per_capita_TEV.loc[phi, vax_policy]   = natl_per_capita_TEV.loc[phi, vax_policy]   + f["per_capita_TEV"]  * nw
                natl_per_capita_VSLY.loc[phi, vax_policy]  = natl_per_capita_VSLY.loc[phi, vax_policy]  + f["per_capita_VSLY"] * nw

            os.remove(f"/tmp/{filename}") 
    

def run_aggregation_natl(experiment_tag):
    pass
