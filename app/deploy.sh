#!/bin/bash 

# gcloud config set run/region us-central1

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SCRIPT_DIR=${SCRIPT_DIR:-$(pwd)}
tag=$(grep experiment_tag "${SCRIPT_DIR}"/../app/main.py | cut -d '"' -f2 | tr _ -)
gcloud builds submit --tag gcr.io/adaptive-control/vaccine-allocation:"${tag}"
gcloud run deploy vaccine-allocation\
    --image gcr.io/adaptive-control/vaccine-allocation:"${tag}"\
    --tag "${tag}"\
    --no-traffic \
    --no-allow-unauthenticated \
    --platform managed