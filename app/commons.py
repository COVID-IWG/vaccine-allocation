import numpy as np
import pandas as pd
from epimargin.utils import annually, percent, years
from google.cloud import storage

# cloud parameters
bucket_name        = "vaccine-allocation"
bucket             = storage.Client().bucket(bucket_name)

# read in common data at container start
bucket.blob("commons/all_india_coalesced_scaling_Apr15.csv")\
    .download_to_filename("/tmp/initial_conditions.csv")
initial_conditions = pd.read_csv("/tmp/initial_conditions.csv")\
    .drop(columns = ["Unnamed: 0", "Rt_upper", "Rt_lower"])\
    .set_index(["state_code", "district"])

natl_weights  = initial_conditions.filter(regex = "N_[0-9]", axis = 1)\
    .apply(lambda df: df/df.sum())
state_weights = initial_conditions.filter(regex = "N_[0-9]", axis = 1)\
    .groupby(level = 0)\
    .apply(lambda df: df/df.sum())

# simulation settings
simulation_start  = pd.Timestamp("April 15, 2021")
num_sims          = 1000
simulation_range  = 1 * years 
phi_points        = [_ * percent * annually for _ in (25, 50, 100, 200)]
random_seed       = 0
coalesce_states   = ["Delhi", "Manipur", "Dadra And Nagar Haveli And Daman And Diu", "Andaman And Nicobar Islands"]

# model settings
gamma             = 0.1
infectious_period = 1/gamma
agebin_labels     = ["0-17", "18-29","30-39", "40-49", "50-59", "60-69","70+"]
median_ages       = np.array([9, 24, 35, 45, 55, 65, 85])

# serology, etc data 
IN_age_structure = { # WPP2019_POP_F01_1_POPULATION_BY_AGE_BOTH_SEXES
    "0-17":   116880 + 117982 + 126156 + 126046,
    "18-29":  122505 + 117397,
    "30-39":  112176 + 103460,
    "40-49":   90220 +  79440,
    "50-59":   68876 +  59256,
    "60-69":   48891 +  38260,
    "70+":     24091 +  15084 +   8489 +   3531 + 993 + 223 + 48,
}

TN_age_structure = { 
    "0-17" : 15581526,
    "18-29": 15674833,
    "30-39": 11652016,
    "40-49":  9777265,
    "50-59":  6804602,
    "60-69":  4650978,
    "70+":    2858780,
}

N_j = np.array([20504724, 15674833, 11875848, 9777265, 6804602, 4650978, 2858780])

# from Cai et al. 
TN_IFRs = { 
    "0-17" : 0.00003,
    "18-29": 0.00003,
    "30-39": 0.00010,
    "40-49": 0.00032,
    "50-59": 0.00111,
    "60-69": 0.00264,
    "70+"  : 0.00588,
}

# from O'Driscoll et al.; provided by Cai and team at DDL
OD_IFRs = {
    '0-17': 1.5075554e-05,
    '18-29': 8.191095e-05,
    '30-39': 0.00028344113,
    '40-49': 0.0008762423,
    '50-59': 0.0027091566,
    '60-69': 0.0083770715,
    '70+'  : 0.080121934
}

TN_age_structure_norm = sum(TN_age_structure.values())
TN_age_ratios = np.array([v/TN_age_structure_norm for v in TN_age_structure.values()])

# redefined estimators
TN_death_structure = pd.Series({ 
    "0-17" : 32,
    "18-29": 121,
    "30-39": 368,
    "40-49": 984,
    "50-59": 2423,
    "60-69": 3471,
    "70+"  : 4339,
})

TN_recovery_structure = pd.Series({ 
    "0-17": 5054937,
    "18-29": 4819218,
    "30-39": 3587705,
    "40-49": 3084814,
    "50-59": 2178817,
    "60-69": 1313049,
    "70+": 738095,
})

TN_infection_structure = TN_death_structure + TN_recovery_structure
fS = pd.Series(TN_age_ratios)[:, None]
fD = (TN_death_structure     / TN_death_structure    .sum())[:, None]
fR = (TN_recovery_structure  / TN_recovery_structure .sum())[:, None]
fI = (TN_infection_structure / TN_infection_structure.sum())[:, None]