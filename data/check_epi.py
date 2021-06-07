import pandas as pd
from pathlib import Path
from google.cloud import storage

client = storage.Client()
folder = "epi"
# folder = "tev"

try:
    pwd = Path(__file__).parent
except Exception:
    pwd = Path(".")

df = pd.read_csv(pwd / "all_india_coalesced_initial_conditionsApr15.csv")\
    [["state_code", "district"]]

missing = 0
with (pwd / "missing_epi").open("w") as f:
    for (state_code, district) in df.itertuples(index = False):
        if state_code in ["MZ", "WB"]:
            continue
        filecount = len(list(client.list_blobs("vaccine-allocation", prefix = f"main/{folder}/{state_code}/{district}/")))
        if filecount != 13:
            missing += 1
            print(f"{state_code} {district}")
            print(f"{state_code} {district}", file = f)

print("missing", missing)
