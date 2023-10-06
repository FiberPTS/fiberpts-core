// Standard library headers
// TODO: Find and remove libraries that are unnecessary
// TODO: Fix logging (program_name)
#include <errno.h>
#include <gpiod.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

// Local project headers
#include "utility/log_utils.h"
#include "utility/signal_utils.h"
#include "utility/utils.h"

// Unknown libraries
// #include <fcntl.h>
// #include <signal.h>

// Constants
#define SENSOR_LINE_NUMBER 80 // GPIO Line number
#define DEBOUNCE_TIME 1000 // Debounce time in milliseconds
#define VOLTAGE_VALUE 1 // Voltage value corresponding to button press

// File paths and names
const char *FIFO_PATH = "/tmp/tap_event_handler"; // File path for FIFO pipe
const char *PROGRAM_NAME = "operation_tap_listener.c";

// GPIO Configuration
const char *CHIP_NAME = "gpiochip1"; // Name of the GPIO chip
struct gpiod_chip *chip;
struct gpiod_line *sensor_line;

// State variables
static struct timespec last_release_time; // Time of the last sensor tap
static int sensor_touched = 0; // Flag for whether the sensor registered a tap

/**
 * @brief Initializes GPIO for button input.
 * @return 0 on success, 1 on failure.
 */
int initialize_gpio(void) {
    chip = gpiod_chip_open_by_name(CHIP_NAME);
    if (!chip) {
        perror_log(PROGRAM_NAME, "Open chip failed: ");
        return -1;
    }
    sensor_line = gpiod_chip_get_line(chip, SENSOR_LINE_NUMBER);
    if (!sensor_line) {
        perror_log(PROGRAM_NAME, "Get line failed: ");
        gpiod_chip_close(chip);
        return -1;
    }
    if (gpiod_line_request_input(sensor_line, "button") < 0) {
        perror_log(PROGRAM_NAME, "Request line as input failed: ");
        gpiod_chip_close(chip);
        return -1;
    }
    return 0;
}

/**
 * @brief Releases the GPIO resources.
 */
void cleanup_gpio(void) {
    gpiod_line_release(sensor_line);
    gpiod_chip_close(chip);
}

int main(void) {
    // Initialize SIGINT signal handler with the cleanup function
    if (initialize_signal_handlers(HANDLE_SIGINT | HANDLE_SIGTERM, cleanup_gpio) == -1) {
        perror_log(PROGRAM_NAME, "Error initializing signal handlers: ");
        return 1;
    }

    // Initialize GPIO.
    if (initialize_gpio() == -1) {
        return 1;
    }

    // Initialize the named pipe for IPC
    if (mkfifo(FIFO_PATH, 0666) == -1 && errno != EEXIST) {
        perror_log(PROGRAM_NAME, "Error creating named pipe: ");
        return 1;
    }

    // Sets the last release time
    clock_gettime(CLOCK_MONOTONIC, &last_release_time);

    struct timespec current_time;

    // Main loop to monitor the touch sesnor state.
    while (!interrupted) {
        // Gets the current time
        clock_gettime(CLOCK_MONOTONIC, &current_time);

        // Get current voltage value on the sensor line
        int value = gpiod_line_get_value(sensor_line);

        // Checks the touch sensor state while handling tap & release events.
        // Implements debounce logic to avoid false triggers.
        if (value < 0) {
            perror_log(PROGRAM_NAME, "Read line value failed");
        } else if (value == VOLTAGE_VALUE) {
            if (!is_debounce_time_passed(current_time, last_release_time, DEBOUNCE_TIME)) {
                last_release_time = current_time;
                continue;
            }
            // Register tap if sensor was not touched within the debounce time
            // Get current timestamp
            char timestamp[32];
            get_current_time_in_est(timestamp, "%Y-%m-%d %H:%M:%S");
            // Data to send through pipe
            char data_to_send[strlen(PROGRAM_NAME) + strlen("::") + strlen(timestamp) + 1];
            snprintf(data_to_send, sizeof(data_to_send), "%s::%s", PROGRAM_NAME, timestamp);
            // Send tap data through pipe
            send_data_to_pipe(data_to_send, FIFO_PATH);
            print_log(PROGRAM_NAME, "Button Pressed\n");
            last_release_time = current_time;
        }
    }
    cleanup_gpio();
    return 0;
}