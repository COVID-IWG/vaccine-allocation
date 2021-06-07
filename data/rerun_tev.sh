function run() { 
    curl -s -XPOST \
        -H "Authorization: Bearer $(gcloud auth print-identity-token)"\
        -H 'Content-Type: application/json' \
        "https://vaccine-allocation-sipjq3uhla-uc.a.run.app/${1}"  \
        --data '{"state_code": "'"${2}"'", "district": "'"${3}"'"}'
}

rm logfile_tev

while read -r state_code district; do 
    echo "${state_code} - ${district} -> STARTED"
    (
        result=$(run tev "${state_code}" "${district}");
        echo ${state_code} - ${district} - ${result} >> ./logfile_tev 
    ) &
    sleep 1
done < missing_tev