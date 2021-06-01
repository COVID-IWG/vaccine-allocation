import os
import numpy as np
import pandas as pd
from itertools import product

from commons import (agebin_labels, bucket, coalesce_states, phi_points,
                      simulation_range, simulation_start)

tev_columns = ["state", "N_tot", 'N_0', 'N_1', 'N_2', 'N_3', 'N_4', 'N_5', 'N_6', 'T_ratio']

blobs = ["reg_estimates_india_TRYTHIS.dta", "pcons_2019.dta", "all_india_sero_pop.csv", "life_expectancy_2009_2013_collapsed.dta"]
for blob in blobs:
    bucket.blob(f"commons/{blob}").download_to_filename(f"/tmp/{blob}")

coeffs = pd.read_stata("/tmp/reg_estimates_india_TRYTHIS.dta")\
    [["parm", "estimate", "state_api", "district_api"]]\
    .rename(columns = {"parm": "param", "state_api": "state", "district_api": "district"})\
    .set_index("param")

I_coeff, D_coeff, constant = coeffs.loc[["I", "D", "_cons"]].estimate
month_FE = coeffs.filter(like = "month", axis = 0).estimate.values[
    pd.date_range(
        start   = simulation_start, 
        periods = simulation_range  + 1, 
        freq    = "D").month.values - 1
]
district_FE = coeffs.filter(like = "district", axis = 0)\
    .set_index(["state", "district"])["estimate"].to_dict()

# per capita daily consumption levels 
consumption_2019 = pd.read_stata("/tmp/pcons_2019.dta")\
    .rename(columns = lambda _: _.replace("_api", ""))\
    .set_index(["state", "district"])
district_age_pop = pd.read_csv("/tmp/all_india_sero_pop.csv").set_index(["state", "district"])

# sum up consumption in coalesced states
consumption_2019 = pd.concat(
    [consumption_2019.drop(labels = coalesce_states, axis = 0, level = 0)] + 
    [district_age_pop.loc[state].filter(like = "N_", axis = 1).join(consumption_2019)\
        .assign(**{f"aggcons_{i}": (lambda i: lambda _: _[f"N_{i}"] * _[f"pccons{i+1}"])(i) for i in range(7)})\
        .drop(columns = [f"pccons{i+1}" for i in range(7)])\
        .sum(axis = 0)\
        .to_frame().T\
        .assign(**{f"pccons{i+1}": (lambda i: lambda _: _[f"aggcons_{i}"] / _[f"N_{i}"])(i) for i in range(7)})\
        [consumption_2019.columns]\
        .assign(state = state, district = state)\
        .set_index(["state", "district"])
    for state in coalesce_states]
).sort_index() 

# life expectancy per state
years_life_remaining = pd.read_stata("/tmp/life_expectancy_2009_2013_collapsed.dta")\
    .assign(state = lambda _: _["state"].str.replace("&", "And"))\
    .set_index("state")\
    .rename(columns = {f"life_expectancy{i+1}": agebin_labels[i] for i in range(7)})

def rc_hat(state, district, dI_pc, dD_pc):
    """ estimate consumption decline """
    return (
        district_FE.get((state, district), 0) + constant + 
        month_FE[:, None] + 
        I_coeff * dI_pc   + 
        D_coeff * dD_pc
    )

def NPV(daily, n = simulation_range + 1, beta = 1/((1.0425)**(1/365))):
    """ calculate net present value over n periods at discount factor beta """
    s = np.arange(n)
    return [ 
        np.sum(np.power(beta, s[t:] - t)[:, None, None] * daily[t:, :], axis = 0)
        for t in range(n)
    ]

def policy_TEV(pi, q_p1v0, q_p0v0, c_p1v1, c_p1v0, c_p0v0):
    """ evaluate health and econ metrics for the vaccination policy scenario """
    # overall economic value
    TEV_daily = (1 - pi) * q_p1v0 * c_p1v0 + pi * c_p1v1 
    # health contribution to economic value
    dTEV_hlth = \
        (1 - pi) * (q_p1v0 - q_p0v0.mean(axis = 1)[:, None, :]) * c_p1v0 +\
             pi  * (np.array(1) - q_p0v0.mean(axis = 1)[:, None, :]) * c_p1v1
    # consumption contribution to economic value
    dTEV_cons = \
        (1 - pi) * q_p0v0.mean(axis = 1)[:, None, :] * (c_p1v0 - c_p0v0.mean(axis = 1)[:, None, :]) +\
             pi                                      * (c_p1v1 - c_p0v0.mean(axis = 1)[:, None, :])
    # private contribution to economic value
    dTEV_priv = c_p1v1 - q_p1v0 * c_p1v0
    
    return (
        NPV(TEV_daily),
        NPV(dTEV_hlth)[0],
        NPV(dTEV_cons)[0],
        NPV(dTEV_priv)[0]
    )

def policy_VSLY(pi, q_p1v1, q_p1v0, c_p0v0):
    # value of statistical life year
    return NPV((((1 - pi) * q_p1v0) + (pi * q_p1v1)) * np.mean(c_p0v0, axis = 1)[:, None, :])

def policy_VSL(LS, age_weight, c_p0v0):
    return (LS.sum(axis = 1) * (age_weight * NPV(c_p0v0)[0]).sum(axis = 1))

def counterfactual_metrics(q_p0v0, c_p0v0):
    """ evaluate health and econ metrics for the non-vaccination policy scenario """
    TEV_daily  = q_p0v0 * c_p0v0
    VSLY_daily = q_p0v0 * np.mean(c_p0v0, axis = 1)[:, None, :]
    return NPV(TEV_daily), NPV(VSLY_daily)

def save_metrics(filename, **metrics):
    np.savez_compressed(f"{filename}.npz", **metrics)

def run_evaluation(state_code, district, population_data, experiment_tag):
    state, N_district, N_0, N_1, N_2, N_3, N_4, N_5, N_6, T_ratio = population_data
    N_jk = np.array([N_0, N_1, N_2, N_3, N_4, N_5, N_6])

    rc_hat_p1v1 = rc_hat(state, district, np.zeros((simulation_range + 1, 1)), np.zeros((simulation_range + 1, 1)))
    c_p1v1 = np.transpose(
        (1 + rc_hat_p1v1)[:, None] * consumption_2019.loc[state, district].values[:, None],
        [0, 2, 1]
    )

    state_years_life_remaining = years_life_remaining.get(state, default = years_life_remaining.mean(axis = 0))
    phi_p0 = int(phi_points[0] * 365 * 100)
    cf_tag = f"{state_code}_{district}_phi{phi_p0}_novax"

    print(f"{state_code}/{district}/tev: downloading counterfactual simulation data")
    bucket.blob(f"{experiment_tag}/epi/{state_code}/{district}/{cf_tag}.npz")\
        .download_to_filename(f"/tmp/simulations_{state_code}_{district}_{cf_tag}.npz")
    with np.load(f"/tmp/simulations_{state_code}_{district}_{cf_tag}.npz") as counterfactual:
        dI_pc_p0 = counterfactual['dT']/(N_district * T_ratio)
        dD_pc_p0 = counterfactual['dD']/(N_district)
        q_p0v0   = counterfactual["q0"]
        D_p0     = counterfactual["Dj"]
    os.remove(f"/tmp/simulations_{state_code}_{district}_{cf_tag}.npz")

    rc_hat_p0v0 = rc_hat(state, district, dI_pc_p0, dD_pc_p0)
    c_p0v0 = np.transpose(
        (1 + rc_hat_p0v0) * consumption_2019.loc[state, district].values[:, None, None],
        [1, 2, 0]
    )

    print(f"{state_code}/{district}/tev: saving counterfactual policy metrics")
    TEV_p0, VSLY_p0 = counterfactual_metrics(q_p0v0, c_p0v0)
    save_metrics(
        f"/tmp/metrics_{state_code}_{district}_{cf_tag}", 
        deaths          = (D_p0[-1] - D_p0[0]).sum(axis = 1),
        YLL             = (D_p0[-1] - D_p0[0]) @ state_years_life_remaining,
        per_capita_TEV  =  TEV_p0,
        per_capita_VSLY = VSLY_p0,
        total_TEV       = N_jk *  TEV_p0,
        total_VSLY      = N_jk * VSLY_p0
    )
    bucket.blob(f"{experiment_tag}/tev/{state_code}/{district}/metrics_{cf_tag}.npz")\
        .upload_from_filename(f"/tmp/metrics_{state_code}_{district}_{cf_tag}.npz")
    os.remove(f"/tmp/metrics_{state_code}_{district}_{cf_tag}.npz")

    for (phi, vax_policy) in product([int(_*365*100) for _ in phi_points], ["random", "contact", "mortality"]):
        print(f"{state_code}/{district}/tev: downloading phi = {phi}, {vax_policy} simulation data")
        p1_tag = f"{state_code}_{district}_phi{phi}_{vax_policy}"

        bucket.blob(f"{experiment_tag}/epi/{state_code}/{district}/{p1_tag}.npz")\
            .download_to_filename(f"/tmp/simulations_{state_code}_{district}_{p1_tag}.npz")
        with np.load(f"/tmp/simulations_{state_code}_{district}_{p1_tag}.npz") as policy:
            dI_pc_p1 = policy['dT']/(N_district * T_ratio)
            dD_pc_p1 = policy['dD']/(N_district)
            pi       = policy['pi'] 
            q_p1v0   = policy['q0']
            D_p1     = policy["Dj"]
        os.remove(f"/tmp/simulations_{state_code}_{district}_{p1_tag}.npz")

        rc_hat_p1v0 = rc_hat(state, district, dI_pc_p1, dD_pc_p1)
        c_p1v0 = np.transpose(
            (1 + rc_hat_p1v0) * consumption_2019.loc[state, district].values[:, None, None], 
            [1, 2, 0]
        )

        LS = ((D_p0[-1] - D_p0[0])) - (D_p1[-1] - D_p1[0])
        # VSL = policy_VSL(LS, age_weight, c_p0v0)
        TEV_p1, dTEV_health, dTEV_cons, dTEV_priv = policy_TEV(pi, q_p1v0, q_p0v0, c_p1v1, c_p1v0, c_p0v0)
        VSLY_p1 = policy_VSLY(pi, np.array(1), q_p1v0,  c_p0v0)

        print(f"{state_code}/{district}/tev: saving phi = {phi}, {vax_policy} metrics")
        save_metrics(
            f"/tmp/metrics_{state_code}_{district}_{p1_tag}",
            deaths          = (D_p1[-1] - D_p1[0]).sum(axis = 1),
            YLL             = (D_p1[-1] - D_p1[0]) @ state_years_life_remaining,
            per_capita_TEV  = TEV_p1,
            per_capita_VSLY = VSLY_p1,
            total_TEV       = TEV_p1  * N_jk,
            total_VSLY      = VSLY_p1 * N_jk
        )
        bucket.blob(f"{experiment_tag}/tev/{state_code}/{district}/metrics_{p1_tag}.npz")\
            .upload_from_filename(f"/tmp/metrics_{state_code}_{district}_{p1_tag}.npz")
        os.remove(f"/tmp/metrics_{state_code}_{district}_{p1_tag}.npz")

        if phi == 50 and vax_policy == "random":
            print(f"{state_code}/{district}/tev: saving econonomic value decompositions")
            save_metrics(
                f"/tmp/decomposition_{state_code}_{district}", 
                dTEV_health = dTEV_health,
                dTEV_cons   = dTEV_cons,
                dTEV_priv   = dTEV_priv,
                dTEV_extn   = (TEV_p1[0] - TEV_p0[0]) - dTEV_priv,
            )
            bucket.blob(f"{experiment_tag}/tev/{state_code}/{district}/decomposition.npz")\
                .upload_from_filename(f"/tmp/decomposition_{state_code}_{district}.npz")
            os.remove(f"/tmp/decomposition_{state_code}_{district}.npz")

