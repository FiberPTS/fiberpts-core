#!/bin/bash

# This tells the shell to exit the script if any command within the script exits with a non-zero status
set -e

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
# TODO: Rename device-id to hostname-id, and create an 'allocated' (bool) column that indicates whether a certain device ID is taken or not
# TODO: Get 'hostname-id' and 'allocated', iterate over them. Keep count of records. If allocated is false, then take the ID and assign it 
# to device's hostname. If no available IDs are found, then use count to create new ID. 
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