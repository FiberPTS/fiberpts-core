#!/bin/bash

# This tells the shell to exit the script if any command within the script exits with a non-zero status
set -e

readonly TABLE=devices
readonly COLUMNS=device_id,allocated

# TODO: Add support for race conditions
get_new_device_id() {
    local response
    response=$(
        curl "${DATABASE_URL}/rest/v1/${TABLE}?select=${COLUMNS}" \
        -H "apikey: ${DATABASE_API_KEY}" \
        -H "Authorization: Bearer ${DATABASE_API_KEY}" \
        -H "Content-Type: application/json"
    )

    local device_id="fpts-"
    local count=0
    while read -r record; do
        local is_allocated
        is_allocated=$(echo "${record}" | jq -r '.allocated')

        if [[ "${is_allocated}" == false ]]; then
            # Assumes correct formatting is used in table records
            device_id=$(echo "${record}" | jq -r '.device_id')
            break
        fi

        count=$((count + 1))
    done < <(echo "${response}" | jq -c '.[]')

    if [[ ${device_id} == "fpts-" ]]; then
        device_id+=$((count + 1))
    fi

    echo "${device_id}"
}

insert_device_id() {
    local device_id=$1
    local response
    response=$(
        curl -X POST "${DATABASE_URL}/rest/v1/${TABLE}" \
        -H "apikey: ${DATABASE_API_KEY}" \
        -H "Authorization: Bearer ${DATABASE_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{ \"device_id\": \"${device_id}\", \"allocated\": true }"
    )
    echo "${response}"
}

main() {
    local device_id
    device_id=$(get_new_device_id)
    readonly device_id
    
    insert_device_id "${device_id}"
    hostnamectl set-hostname "${device_id}" > /dev/null
    return 0
}

main