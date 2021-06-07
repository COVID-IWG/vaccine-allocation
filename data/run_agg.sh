function run() { 
    curl -s -XPOST \
        -H "Authorization: Bearer $(gcloud auth print-identity-token)"\
        -H 'Content-Type: application/json' \
        "https://vaccine-allocation-sipjq3uhla-uc.a.run.app/${1}"  \
        --data '{"state_code": "'"${2}"'"}'
}

rm logfile_agg

cut -d, -f2 all_india_coalesced_initial_conditionsApr15.csv | grep -v "state_code" | uniq |
while read -r state_code; 
for state_code in AN AP AR AS BR CH CT DNDD DL GA ; 
do 
    echo "${state_code} -> STARTED"
    (
        result=$(run agg "${state_code}");
        echo ${state_code} - ${result} >> ./logfile_agg 
    ) &
    sleep 1
done 