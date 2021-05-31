#!/bin/bash 

# gcloud config set run/region us-central1

function run() { 
    curl -s -XPOST \
        -H "Authorization: Bearer $(gcloud auth print-identity-token)"\
        -H 'Content-Type: application/json' \
        "https://${1}---vaccine-allocation-sipjq3uhla-uc.a.run.app/${2}"  \
        --data '{"state_code": "'"${3}"'", "district": "'"${4}"'"}'
}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

if [ $# -eq 0 ]; then 
    filter="*" # no filter 
else 
    filter=${*/ /\\\|/} # concatenate script args with | 
fi

grep "${filter}" "${SCRIPT_DIR}"/../app/data/all_india_coalesced_initial_conditionsApr15.csv | cut -d, -f 2,4 | tr , " " |
while read -r state_code district; do 
    echo "${tag} ${state_code} - ${district} -> STARTED"        &&
    run  "${tag}" epi "${state_code}" "${district}" > /dev/null &&
    run  "${tag}" tev "${state_code}" "${district}" > /dev/null && 
    echo "${tag} ${state_code} - ${district} <- DONE" 
done 