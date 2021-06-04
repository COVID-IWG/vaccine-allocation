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
            print(f"{state_code}/agg: processing {blob.name}")
            *_, district, filename = blob.name.split("/")
            *_, phi, vax_policy    = filename.replace("phi", "").replace(".npz", "").split("_")
            phi = int(phi)

            sw = state_weights.loc[state_code, district]
            nw = natl_weights .loc[state_code, district]
            
            blob.download_to_filename(f"/tmp/{filename}")
            with np.load(f"/tmp/{filename}") as f:
                deaths[phi, vax_policy]                = deaths[phi, vax_policy]                + f["deaths"]
                YLL[phi, vax_policy]                   = YLL[phi, vax_policy]                   + f["YLL"]
                total_TEV[phi, vax_policy]             = total_TEV[phi, vax_policy]             + f["total_TEV"]
                total_VSLY[phi, vax_policy]            = total_VSLY[phi, vax_policy]            + f["total_VSLY"]
                state_per_capita_TEV[phi, vax_policy]  = state_per_capita_TEV[phi, vax_policy]  + f["per_capita_TEV"]  * sw[None, None, :]
                state_per_capita_VSLY[phi, vax_policy] = state_per_capita_VSLY[phi, vax_policy] + f["per_capita_VSLY"] * sw[None, None, :]
                natl_per_capita_TEV[phi, vax_policy]   = natl_per_capita_TEV[phi, vax_policy]   + f["per_capita_TEV"]  * nw[None, None, :]
                natl_per_capita_VSLY[phi, vax_policy]  = natl_per_capita_VSLY[phi, vax_policy]  + f["per_capita_VSLY"] * nw[None, None, :]

            os.remove(f"/tmp/{filename}") 
    
    for (label, outcome) in {
        "deaths"               : deaths,
        "YLL"                  : YLL,
        "total_TEV"            : total_TEV,
        "total_VSLY"           : total_VSLY,
        "state_per_capita_TEV" : state_per_capita_TEV,
        "state_per_capita_VSLY": state_per_capita_VSLY,
        "natl_per_capita_TEV"  : natl_per_capita_TEV,
        "natl_per_capita_VSLY" : natl_per_capita_VSLY
    }.items():
        print(f"{state_code}/agg: uploading aggregated {label.replace('_', ' ')}")
        outfile = f"/tmp/{state_code}_{label}.npz"
        np.savez_compressed(outfile, **{"_".join(map(str, k)): v for (k, v) in outcome.items()})
        bucket.blob(f"{experiment_tag}/agg/{state_code}/{label}.npz")\
            .upload_from_filename(outfile)
        os.remove(outfile)


def run_aggregation_natl(experiment_tag):
    deaths                = empty_dict()
    YLL                   = empty_dict()
    total_TEV             = empty_dict()
    total_VSLY            = empty_dict()
    natl_per_capita_TEV   = empty_dict()
    natl_per_capita_VSLY  = empty_dict()

    for blob in bucket.list_blobs(prefix = f"{experiment_tag}/agg/"):
        if 'state_' in blob.name:
            print(f"NATL/agg: skipping {blob.name}")
            continue
        print(f"NATL/agg: processing {blob.name}")
        *_, state_code, filename = blob.name.split("/")
        outcome = filename.split(".")
        blob.download_to_filename(f"/tmp/{state_code}_{outcome}.npz")
        with np.load(f"/tmp/{state_code}_{outcome}.npz") as f:
            for k_tag in f.files:
                phi, vax_policy = k_tag.split("_")
                phi = int(phi)
                if   outcome == "deaths":               deaths[phi, vax_policy]               = deaths[phi, vax_policy]               + f[k_tag]
                elif outcome == "YLL":                  YLL[phi, vax_policy]                  = YLL[phi, vax_policy]                  + f[k_tag]
                elif outcome == "total_TEV":            total_TEV[phi, vax_policy]            = total_TEV[phi, vax_policy]            + f[k_tag]
                elif outcome == "total_VSLY":           total_VSLY[phi, vax_policy]           = total_VSLY[phi, vax_policy]           + f[k_tag]
                elif outcome == "natl_per_capita_TEV":  natl_per_capita_TEV[phi, vax_policy]  = natl_per_capita_TEV[phi, vax_policy]  + f[k_tag]
                elif outcome == "natl_per_capita_VSLY": natl_per_capita_VSLY[phi, vax_policy] = natl_per_capita_VSLY[phi, vax_policy] + f[k_tag]
        os.remove(f"/tmp/{state_code}_{outcome}.npz")
    
    for (label, outcome) in {
        "deaths"               : deaths,
        "YLL"                  : YLL,
        "total_TEV"            : total_TEV,
        "total_VSLY"           : total_VSLY,
        "natl_per_capita_TEV"  : natl_per_capita_TEV,
        "natl_per_capita_VSLY" : natl_per_capita_VSLY
    }.items():
        print(f"NATL/agg: uploading aggregated {label.replace('_', ' ')}")
        outfile = f"/tmp/NATL_{label}.npz"
        np.savez_compressed(outfile, **{"_".join(map(str, k)): v for (k, v) in outcome.items()})
        bucket.blob(f"{experiment_tag}/agg/NATL/{label}.npz")\
            .upload_from_filename(outfile)
        os.remove(outfile)
