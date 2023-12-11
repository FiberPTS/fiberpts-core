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
    fi
}

set_ownership_and_permissions() {
    # Set group ownership to relevant files
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/src || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/scripts/run || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/config || return 1
    chown :"$GROUP_NAME" "$PROJECT_PATH"/.env.shared || return 1
    chown :"$GROUP_NAME" "$PROJECT_PATH"/.env || return 1
    chown -R :"$GROUP_NAME" "$PROJECT_PATH"/app || return 1

    # Set executable permissions
    # TODO: This is done after shebang is added to all source files when the scripts can be executed after activating the virtual environment (no absolute path execution)
    # find "$PROJECT_PATH"/src -type f -name "*.py" ! -name "__init__.py" -exec chmod 770 {} \; || return 1
    find "$PROJECT_PATH"/scripts/run -type f -name "*.sh" -exec chmod 770 {} \; || return 1
    chmod -R 770 "$PROJECT_PATH"/app || return 1

    # Set readable permissions
    find "$PROJECT_PATH"/config -type f -name "*.py" ! -name "__init__.py" -exec chmod 440 {} \; || return 1
    chmod 440 "$PROJECT_PATH"/.env || return 1

    # Set readable/writable permissions
    chmod 660 "$PROJECT_PATH"/.env.shared || return 1 # Need writable for init.sh script to modify DISPLAY_FRAME_BUFFER_PATH

    echo "Group ownership and permissions set"
}

main() {
    assert_conditions
    add_application_user || { echo "Failed to add user."; exit 1; }
    create_and_assign_group || { echo "Failed to create and assign group."; exit 1; }
    set_ownership_and_permissions || { echo "Failed to set ownership and permissions."; exit 1; }
}

main
