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
    # Check if user already exists
    if id "$USERNAME" &>/dev/null; then
        echo "User $USERNAME already exists. Skipping user creation."
    else
        adduser "$USERNAME" --disabled-password --gecos "" || return 1
        # Running a subshell for setting the username and password securely
        bash -c 'echo "$1:$2" | chpasswd' bash "$USERNAME" "$PASSWORD" || return 1
        echo "User created and password set."
    fi
}

create_and_assign_group() {
    # Check if group already exists
    if getent group "$GROUP_NAME" &>/dev/null; then
        echo "Group $GROUP_NAME already exists. Skipping group creation."
    else
        groupadd "$GROUP_NAME" || return 1
        usermod -a -G "$GROUP_NAME" "$USERNAME" || return 1
        # Add to any other necessary groups
        usermod -a -G video "$USERNAME" || return 1
        usermod -a -G gpio "$USERNAME" || return 1
    fi
}

# Function to set group ownership
set_group_ownership() {
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/src || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/scripts || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/config || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/app || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/venv || return 1

    echo "Group ownership set"
}

set_permissions() {
    # App directory permissions
    chmod -R 770 "$PROJECT_PATH"/app || return 1
    chmod 640 "$PROJECT_PATH"/app/.env || return 1
    chmod 660 "$PROJECT_PATH"/app/.env.shared || return 1
    chmod 660 "$PROJECT_PATH"/app/device_state.json || return 1
    chmod 660 "$PROJECT_PATH"/app/pipes/* || return 1

    # Config directory permissions
    chmod -R 750 "$PROJECT_PATH"/config || return 1
    chmod 640 "$PROJECT_PATH"/config/* || return 1

    # Custom directory permissions
    chmod -R 700 "$PROJECT_PATH"/custom || return 1
    chmod 600 "$PROJECT_PATH"/custom/* || return 1

    # Scripts directory permissions
    chmod -R 770 "$PROJECT_PATH"/scripts || return 1
    chmod 750 "$PROJECT_PATH"/scripts/run/* || return 1
    chmod 750 "$PROJECT_PATH"/scripts/setup/* || return 1
    chmod 700 "$PROJECT_PATH"/scripts/setup.sh || return 1

    # Services directory permissions
    chmod -R 700 "$PROJECT_PATH"/services || return 1
    chmod 600 "$PROJECT_PATH"/services/* || return 1

    # Source code permissions
    chmod -R 750 "$PROJECT_PATH"/src || return 1

    # Test directory permissions
    chmod -R 700 "$PROJECT_PATH"/tests || return 1

    # Virtual environment permissions
    chmod -R 750 "$PROJECT_PATH"/venv || return 1

    # Requirement file permissions
    chmod 660 "$PROJECT_PATH"/requirements.txt || return 1

    echo "File permissions set"
}

main() {
    assert_conditions
    add_application_user || { echo "Failed to add user."; exit 1; }
    create_and_assign_group || { echo "Failed to create and assign group."; exit 1; }
    set_group_ownership || { echo "Failed to set ownership."; exit 1; }
    set_permissions || { echo "Failed to set file permissions."; exit 1; }
}

main
