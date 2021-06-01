from pathlib import Path

import numpy as np
from epimargin.models import Age_SIRVD
from epimargin.utils import normalize

from commons import (bucket, OD_IFRs, fD, fI, fR, infectious_period, num_sims,
                      phi_points, random_seed, simulation_range)

epi_columns = ["sero_0", "N_0", "sero_1", "N_1", "sero_2", "N_2", "sero_3", "N_3", "sero_4", "N_4", "sero_5", "N_5", "sero_6", "N_6", "N_tot", "Rt", "S0", "I0", "R0", "D0", "dT0", "dD0", "V0"]

dst = Path("/tmp")

MORTALITY   = [6, 5, 4, 3, 2, 1, 0]
CONTACT     = [1, 2, 3, 4, 0, 5, 6]
CONSUMPTION = [4, 5, 6, 3, 2, 1, 0]

def prioritize(num_doses, S, prioritization):
    Sp = S[:, prioritization]
    dV = np.where(Sp.cumsum(axis = 1) <= num_doses, Sp, 0)
    dV[np.arange(len(dV)), (Sp.cumsum(axis = 1) > dV.cumsum(axis = 1)).argmax(axis = 1)] = num_doses - dV.sum(axis = 1)
    return dV[:, sorted(range(len(prioritization)), key = prioritization.__getitem__)].clip(0, S)

def save_metrics(tag, policy, dst):
    np.savez_compressed(dst/f"{tag}.npz", 
        dT = policy.dT_total,
        dD = policy.dD_total,
        pi = policy.pi,
        q0 = policy.q0,
        q1 = policy.q1, 
        Dj = policy.D
    )

def run_simulation(state_code, district, initial_conditions, experiment_tag):
    (sero_0, N_0, sero_1, N_1, sero_2, N_2, sero_3, N_3, sero_4, N_4, sero_5, N_5, sero_6, N_6, N_tot, Rt, S0, I0, R0, D0, dT0, dD0, V0) = initial_conditions
    Sj0 = np.array([(1 - sj) * Nj for (sj, Nj) in zip([sero_0, sero_1, sero_2, sero_3, sero_4, sero_5, sero_6], [N_0, N_1, N_2, N_3, N_4, N_5, N_6])])
    Sj0 = prioritize(V0, Sj0.copy()[None, :], MORTALITY)[0]
    def get_model(seed = 0):
        model = Age_SIRVD(
            name        = state_code + "_" + district, 
            population  = N_tot - D0, 
            dT0         = (np.ones(num_sims) * dT0).astype(int), 
            Rt0         = 0 if S0 == 0 else Rt * N_tot / S0,
            S0          = np.tile( Sj0,        num_sims).reshape((num_sims, -1)),
            I0          = np.tile((fI * I0).T, num_sims).reshape((num_sims, -1)),
            R0          = np.tile((fR * R0).T, num_sims).reshape((num_sims, -1)),
            D0          = np.tile((fD * D0).T, num_sims).reshape((num_sims, -1)),
            mortality   = np.array(list(OD_IFRs.values())),
            infectious_period = infectious_period,
            random_seed = seed,
        )
        model.dD_total[0] = np.ones(num_sims) * dD0
        model.dT_total[0] = np.ones(num_sims) * dT0
        return model

    for phi in phi_points:
        print(f"{state_code}/{district}/epi: running simulation for phi = {phi * 365 * 100}")
        num_doses = phi * (S0 + I0 + R0)
        sim_tag = f"{state_code}_{district}_phi{int(phi * 365 * 100)}_"
        random_model, mortality_model, contact_model, no_vax_model = [get_model(random_seed) for _ in range(4)]
        for t in range(simulation_range):
            if t <= 1/phi:
                dV_random    = num_doses * normalize(random_model.N[-1], axis = 1).clip(0)
                dV_mortality = prioritize(num_doses, mortality_model.N[-1], MORTALITY  ).clip(0) 
                dV_contact   = prioritize(num_doses, contact_model.N[-1],   CONTACT    ).clip(0) 
            else: 
                dV_random, dV_mortality, dV_contact = np.zeros((num_sims, 7)), np.zeros((num_sims, 7)), np.zeros((num_sims, 7))
            
            random_model   .parallel_forward_epi_step(dV_random,    num_sims = num_sims)
            mortality_model.parallel_forward_epi_step(dV_mortality, num_sims = num_sims)
            contact_model  .parallel_forward_epi_step(dV_contact,   num_sims = num_sims)
            no_vax_model   .parallel_forward_epi_step(dV = np.zeros((7, num_sims))[:, 0], num_sims = num_sims)

        if phi == phi_points[0]:
            print(f"{state_code}/{district}/epi: uploading counterfactual simulation")
            save_metrics(sim_tag + "novax", no_vax_model   , dst)
            bucket.blob(f"{experiment_tag}/epi/{state_code}/{district}/{sim_tag}novax.npz").upload_from_filename(str(dst / f"{sim_tag}novax.npz"))
            (dst / f"{sim_tag}novax.npz").unlink(missing_ok = True)
        
        for (model, label) in [(random_model, "random"), (mortality_model, "mortality"), (contact_model, "contact")]:
            print(f"{state_code}/{district}/epi: uploading phi = {phi * 365 * 100}, {label} simulation")
            save_metrics(sim_tag + label, model, dst)
            bucket.blob(f"{experiment_tag}/epi/{state_code}/{district}/{sim_tag}{label}.npz").upload_from_filename(str(dst / f"{sim_tag}{label}.npz"))
            (dst / f"{sim_tag}{label}.npz").unlink(missing_ok = True)
        
    return "OK!"
