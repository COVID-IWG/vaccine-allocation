#!/bin/bash 

# gcloud config set run/region us-central1

# gcloud run services update-traffic vaccine-allocation --platform managed --to-latest
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SCRIPT_DIR=${SCRIPT_DIR:-$(pwd)}
tag=$(grep '^experiment_tag = ' "${SCRIPT_DIR}"/../app/main.py | cut -d '"' -f2 | tr _ -)
echo "tag: ${tag}"
gcloud builds submit --tag gcr.io/adaptive-control/vaccine-allocation:"${tag}"
gcloud run deploy vaccine-allocation\
    --image gcr.io/adaptive-control/vaccine-allocation:"${tag}"\
    --no-allow-unauthenticated \
    --platform managed \
    --memory 8Gi \
    --cpu 2 \
    --concurrency 10 \
    --timeout 900
#    --no-traffic \
#    --tag "${tag}" \
