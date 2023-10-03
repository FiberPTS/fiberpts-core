// Local project headers
#include "log_utils.h"
#include "utils.h"

// Standard library headers
#include <gpiod.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

// Unknown libraries
// #include <fcntl.h>
// #include <signal.h>

// Constants
#define SENSOR_LINE_NUMBER 80 // GPIO Line number
#define DEBOUNCE_TIME 1000 // Debounce time in milliseconds
#define VOLTAGE_VALUE 1 // Voltage value corresponding to button press

// File paths and names
const char *FIFO_PATH = "/tmp/screenPipe"; // File path for FIFO pipe
const char *PROGRAM_NAME = "operation_tap_listener.c"; // Program name

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

/**
 * @brief Checks if debounce time has passed since the last button release.
 * @param current_time The current time.
 * @param last_release The last release time.
 * @return 1 if debounce time has passed, 0 otherwise.
 */
int is_debounce_time_passed(struct timespec current_time, struct timespec last_release) {
    // Convert DEBOUNCE_TIME to seconds and nanoseconds components
    long debounce_sec = DEBOUNCE_TIME / 1000;
    long debounce_nsec = (DEBOUNCE_TIME % 1000) * 1000000;

    // Check if the difference in seconds exceeds the debounce seconds
    if (current_time.tv_sec > last_release.tv_sec + debounce_sec) {
        return 1;
    }

    // Check if the seconds are equal and the difference in nanoseconds exceeds the debounce nanoseconds
    if ((current_time.tv_sec == last_release.tv_sec) &&
        (current_time.tv_nsec > last_release.tv_nsec + debounce_nsec)) {
        return 1;
    }

    return 0;
}

int main(void) {
    // Initialize SIGINT signal handler
    if (initialize_signal_handlers(HANDLE_SIGINT) == -1) {
        perror_log(PROGRAM_NAME, "Error initializing signal handlers: ");
        return 1
    }

    // Initialize GPIO.
    if (initialize_gpio() == -1) {
        return 1;
    }

    // Create a named pipe for inter-process communication.
    if (mkfifo(FIFO_PATH, 0666) == -1) {
        if (errno != EEXIST) {  // EEXIST means the file already exists, which might be okay
            perror_log(PROGRAM_NAME, "Error creating named pipe: ");
            return 1;
        }
    }

    // Main loop to monitor the touch sesnor state.
    while (!interrupted) {
        // Gets the current time
        struct timespec current_time;
        clock_gettime(CLOCK_MONOTONIC, &current_time);

        // Get current voltage value on the sensor line
        int value = gpiod_line_get_value(sensor_line);

        // Checks the touch sensor state while handling tap & release events.
        // Implements debounce logic to avoid false triggers.
        if (value < 0) {
            perror_log(PROGRAM_NAME, "Read line value failed");
        } else if (value == VOLTAGE_VALUE) {
            // Register tap if sensor was not touched within the debounce time
            if (!sensor_touched) {
                // Get current timestamp
                char timestamp[32];
                get_current_time_in_est(timestamp, "%Y-%m-%d %H:%M:%S");
                // Data to send through pipe
                char data_to_send[strlen(PROGRAM_NAME) + strlen("::") + strlen(timestamp) + 1];
                snprintf(data_to_send, sizeof(data_to_send), "%s::%s", PROGRAM_NAME, timestamp);
                // Send tap data through pipe
                send_data_to_pipe(data_to_send, FIFO_PATH);
                print_log(PROGRAM_NAME, "Button Pressed\n");
            }
            // Set flag and last release time
            last_release_time = current_time;
            sensor_touched = 1;
        } else if (sensor_touched && is_debounce_time_passed(current_time, last_release_time)) {
            // Button was just released
            sensor_touched = 0;
        }
    }
    cleanup_gpio();
    return 0;
}