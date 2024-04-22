#!/bin/bash
#
# This script interacts with Supabase to fetch an unallocated device ID, mark
# it as allocated, and then set the system's hostname to this new device ID.

set -e

TABLE=devices
COLUMNS=device_id,allocated

#######################################
# Fetches a new device ID from the database that has not been allocated. If all
# IDs are allocated, generates a new ID based on the count of devices.
# Globals:
#   TABLE, COLUMNS, DATABASE_URL, DATABASE_API_KEY
# Arguments:
#   None
# Outputs:
#   Prints the new or found unallocated device ID to STDOUT.
#######################################
function get_new_device_id() {
  local response
  response=$(
    curl "${DATABASE_URL}/rest/v1/${TABLE}?select=${COLUMNS}" \
      -H "apikey: ${DATABASE_API_KEY}" \
      -H "Authorization: Bearer ${DATABASE_API_KEY}" \
      -H "Content-Type: application/json"
  )
  readonly response

  local device_id="fpts-"
  local count=0
  while read -r record; do
    local is_allocated
    is_allocated=$(echo "${record}" | jq -r '.allocated')

    if [[ "${is_allocated}" == false ]]; then
      # Retrieves the first unallocated device ID
      device_id=$(echo "${record}" | jq -r '.device_id')
      break
    fi

    count=$((count + 1))
  done < <(echo "${response}" | jq -c '.[]')

  if [[ ${device_id} == "fpts-" ]]; then
    # Generates a new device ID if all existing IDs are allocated
    device_id+=$((count + 1))
  fi

  echo "${device_id}"
}

#######################################
# Inserts the given device ID into the database and marks it as allocated.
# Globals:
#   TABLE, DATABASE_URL, DATABASE_API_KEY
# Arguments:
#   device_id - The device ID to be marked as allocated in the database.
# Outputs:
#   Response from the database after inserting the device ID.
#######################################
function insert_device_id() {
  # TODO: Add support for handling race conditions when allocating new device IDs
  local device_id=$1
  local response
  response=$(
    curl -X POST "${DATABASE_URL}/rest/v1/${TABLE}" \
      -H "apikey: ${DATABASE_API_KEY}" \
      -H "Authorization: Bearer ${DATABASE_API_KEY}" \
      -H "Content-Type: application/json" \
      -H "Prefer: return=minimal" \
      -H "Prefer: resolution=merge-duplicates" \
      -d "{ \"device_id\": \"${device_id}\", \"allocated\": true }"
  )
  echo "${response}"
}

#######################################
# Fetches a new or unallocated device ID, marks it as allocated in the database,
# and setting the system's hostname to this ID.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Changes the system's hostname to the new or unallocated device ID.
#######################################
function main() {
  local device_id
  device_id=$(get_new_device_id)
  readonly device_id

  insert_device_id "${device_id}"
  hostnamectl set-hostname "${device_id}"
}

main
