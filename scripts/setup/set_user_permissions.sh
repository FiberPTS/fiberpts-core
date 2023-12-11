#!/bin/bash

assert_conditions() {
    # Validate script is run as root
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi

    # Check for required environment variables
    if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ] || [ -z "$GROUP_NAME" ] || [ -z "$PROJECT_PATH" ]; then
        echo "Required environment variables: USERNAME, PASSWORD, GROUP_NAME, PROJECT_PATH are not all set."
        exit 1
    fi
}

add_application_user() {
    adduser "$USERNAME" --disabled-password --gecos "" || return 1
    # Running a subshell for setting the username and password securely
    sh -c 'echo "$1:$2" | chpasswd' sh "$USERNAME" "$PASSWORD" || return 1
    echo "User created and password set."
}

create_and_assign_group() {
    groupadd "$GROUP_NAME" || return 1
    usermod -a -G "$GROUP_NAME" "$USERNAME" || return 1
    # Add to any other necessary groups
    usermod -a -G video "$USERNAME" || return 1
    
}

set_ownership_and_permissions() {
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/src || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/scripts/run || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/config || return 1
    chown :"$GROUP_NAME" "$PROJECT_PATH"/.env.shared || return 1
    chown :"$GROUP_NAME" "$PROJECT_PATH"/.env || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/app || return 1

    find "$PROJECT_PATH"/src -type f -name "*.py" ! -name "__init__.py" -exec chmod 770 {} \; || return 1
    find "$PROJECT_PATH"/scripts/run -type f -name "*.sh" -exec chmod 770 {} \; || return 1

    find "$PROJECT_PATH"/config -type f -name "*.py" ! -name "__init__.py" -exec chmod 440 {} \; || return 1
    chmod 440 "$PROJECT_PATH"/.env.shared || return 1
    chmod 440 "$PROJECT_PATH"/.env.secure || return 1

    chmod -R 660 "$PROJECT_PATH"/app || return 1
}

main() {
    assert_conditions
    add_application_user || { echo "Failed to add user."; exit 1; }
    create_and_assign_group || { echo "Failed to create and assign group."; exit 1; }
    set_ownership_and_permissions || { echo "Failed to set ownership and permissions."; exit 1; }
}

main
