#!/bin/bash

readonly TABLE=devices
readonly COLUMN=device_id
readonly SUPABASE_URL=https://qfgukdtejvguiqtlqfay.supabase.co

get_new_device_id() {
    # Get the last device ID in the database
    local response=$(
        curl "${SUPABASE_URL}/rest/v1/${TABLE}?select=${COLUMN}&order=${COLUMN}.desc&limit=1" \
        -H "apikey: ${DATABASE_API_KEY}" \
        -H "Authorization: Bearer ${DATABASE_API_KEY}" \
        -H "Content-Type: application/json"
    )

    local device_id
    if [ response = "[]" ]; then
        device_id="fpts-001"
    else
        # Parse JSON and extract first device ID
        last_id=$(echo ${response} | jq -r '.[0].device_id')

        id_num=$(printf "%03d" $((10#${last_id: -3} + 1)))
        device_id="fpts-${id_num}"
    fi

    echo ${device_id}
}

# TODO: Add retry in case device ID is already taken
# TODO: Freeing up a device ID in case a device is re-imaged
#   - Ordering of device ids should not be altered (first available device ID must be
#     fetched instead of the last one)
insert_device_id() {
    local device_id=$1
    local response=$(
        curl -X POST "${SUPABASE_URL}/rest/v1/${TABLE}" \
        -H "apikey: ${DATABASE_API_KEY}" \
        -H "Authorization: Bearer ${DATABASE_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{ \""${COLUMN}"\": \""${device_id}"\" }"
    )
    echo ${response}
}

main() {
    local device_id=$(get_new_device_id)
    readonly device_id
    insert_device_id "${device_id}"
    hostnamectl set-hostname ${device_id}
    return 0
}

main