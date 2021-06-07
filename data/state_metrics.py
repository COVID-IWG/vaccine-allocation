from itertools import islice
from pathlib import Path

import numpy as np
from google.cloud import storage
from matplotlib import pyplot as plt

client = storage.Client()

# deaths
dst_dir = Path("./artifacts/deaths")
dst_dir.mkdir(exist_ok = True)
for blob in islice(filter(lambda blob: "natl" not in blob.name.lower() and "deaths" in blob.name, client.list_blobs("vaccine-allocation", prefix = "main/agg/")), None):
    *_, state, _ = blob.name.split("/")
    print(state)
    dst = dst_dir / f"{state}_deaths.npz"
    blob.download_to_filename(dst)
    deaths = {k.replace(".0", ""): v for (k, v) in np.load(dst).items()}
    plt.scatter(range(len(deaths)), [np.mean(v) for v in deaths.values()])
    plt.xticks(ticks = range(len(deaths)), labels = [_.replace("_", "\n") for _ in deaths.keys()])
    plt.gcf().set_size_inches(11, 8)
    plt.title(f"{state}: deaths")
    plt.savefig(dst_dir / f"{state}_deaths.png", dpi = 600)
    plt.close("all")

# YLL
dst_dir = Path("./artifacts/YLL")
dst_dir.mkdir(exist_ok = True)
for blob in islice(filter(lambda blob: "natl" not in blob.name.lower() and "YLL" in blob.name, client.list_blobs("vaccine-allocation", prefix = "main/agg/")), None):
    *_, state, _ = blob.name.split("/")
    print(state)
    dst = dst_dir / f"{state}_YLL.npz"
    blob.download_to_filename(dst)
    YLL = {k.replace(".0", ""): v for (k, v) in np.load(dst).items()}
    plt.scatter(range(len(YLL)), [np.mean(v) for v in YLL.values()])
    plt.xticks(ticks = range(len(YLL)), labels = [_.replace("_", "\n") for _ in YLL.keys()])
    plt.gcf().set_size_inches(11, 8)
    plt.title(f"{state}: YLL")
    plt.savefig(dst_dir / f"{state}_YLL.png", dpi = 600)
    plt.close("all")

# VSLY
dst_dir = Path("./artifacts/total_VSLY")
dst_dir.mkdir(exist_ok = True)
for blob in islice(filter(lambda blob: "natl" not in blob.name.lower() and "total_VSLY" in blob.name, client.list_blobs("vaccine-allocation", prefix = "main/agg/")), None):
    *_, state, _ = blob.name.split("/")
    print(state)
    dst = dst_dir / f"{state}_total_VSLY.npz"
    blob.download_to_filename(dst)
    total_VSLY = {k.replace(".0", ""): v for (k, v) in np.load(dst).items()}
    plt.scatter(range(len(total_VSLY)), [np.mean(v) for v in total_VSLY.values()])
    plt.xticks(ticks = range(len(total_VSLY)), labels = [_.replace("_", "\n") for _ in total_VSLY.keys()])
    plt.gcf().set_size_inches(11, 8)
    plt.title(f"{state}: total_VSLY")
    plt.savefig(dst_dir / f"{state}_total_VSLY.png", dpi = 600)
    plt.close("all")

# TEV 
dst_dir = Path("./artifacts/total_TEV")
dst_dir.mkdir(exist_ok = True)
for blob in islice(filter(lambda blob: "natl" not in blob.name.lower() and "total_TEV" in blob.name, client.list_blobs("vaccine-allocation", prefix = "main/agg/")), None):
    *_, state, _ = blob.name.split("/")
    print(state)
    dst = dst_dir / f"{state}_total_TEV.npz"
    blob.download_to_filename(dst)
    total_TEV = {k.replace(".0", ""): v for (k, v) in np.load(dst).items()}
    plt.scatter(range(len(total_TEV)), [np.mean(v) for v in total_TEV.values()])
    plt.xticks(ticks = range(len(total_TEV)), labels = [_.replace("_", "\n") for _ in total_TEV.keys()])
    plt.gcf().set_size_inches(11, 8)
    plt.title(f"{state}: total_TEV")
    plt.savefig(dst_dir / f"{state}_total_TEV.png", dpi = 600)
    plt.close("all")

# MH
dst_dir = Path("./artifacts/MH")
dst_dir.mkdir(exist_ok = True)
for blob in islice(client.list_blobs("vaccine-allocation", prefix = "main/epi/MH"), None):
    if 'novax' in blob.name:
        blob.download_to_filename(dst_dir / blob.name.split("/")[-1])
        filename = dst_dir / blob.name.split("/")[-1]
        new_cases = np.load(filename)["dT"]
        district = blob.name.split("/")[3]
        plt.plot(np.mean(new_cases, axis = 1))
        plt.title(f"{district}: new cases (mean)")
        plt.show()

# KL
dst_dir = Path("./artifacts/KL")
dst_dir.mkdir(exist_ok = True)
for blob in islice(client.list_blobs("vaccine-allocation", prefix = "main/epi/KL"), None):
    if 'novax' in blob.name:
        blob.download_to_filename(dst_dir / blob.name.split("/")[-1])
        filename = dst_dir / blob.name.split("/")[-1]
        new_cases = np.load(filename)["dT"]
        district = blob.name.split("/")[3]
        plt.plot(np.mean(new_cases, axis = 1))
        plt.title(f"{district}: new cases (mean)")
        plt.show()


# CT
dst_dir = Path("./artifacts/CT")
dst_dir.mkdir(exist_ok = True)
for blob in islice(client.list_blobs("vaccine-allocation", prefix = "main/epi/CT"), None):
    if 'novax' in blob.name:
        # blob.download_to_filename(dst_dir / blob.name.split("/")[-1])
        filename = dst_dir / blob.name.split("/")[-1]
        new_cases = np.load(filename)["dD"]
        district = blob.name.split("/")[3]
        plt.plot(np.mean(new_cases, axis = 1))
        plt.title(f"{district}: new deaths (mean)")
        plt.show()
