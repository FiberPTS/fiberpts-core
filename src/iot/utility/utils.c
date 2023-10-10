#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>

// TODO: Fix logging (program_name)
// TODO: Find and remove libraries that are unnecessary

/**
 * @brief Retrieves the device's unique ID.
 * @return A string containing the device's ID or NULL on failure.
 */
char *get_device_id() {
    FILE *file = fopen("/etc/device-id", "r");
    if (file == NULL) {
        perror("Unable to open /etc/device-id");
        return NULL;
    }

    char *device_id = malloc(33);
    if (fgets(device_id, 33, file) == NULL) {
        perror("Unable to read /etc/device-id");
        fclose(file);
        free(device_id);
        return NULL;
    }

    fclose(file);
    return device_id;
}

/**
 * @brief Sends data to a program via a FIFO pipe.
 * @param data The data to send.
 * @param fifo_path The file path of the FIFO pipe.
 */
void send_data_to_pipe(const char *data, const char *fifo_path) {
    int fd;
    fd = open(fifo_path, O_WRONLY);
    if (fd == -1) {
        perror("Could not open pipe");
        return;
    }
    write(fd, data, strlen(data) + 1);
    close(fd);
}

/**
 * @brief Retrieves the current time in the EST timezone and formats it.
 * @param buffer A buffer to store the formatted time string.
 * @param format A format string compatible with strftime.
 */
void get_current_time_in_est(char *buffer, const char *format) {
    // Set timezone to EST
    setenv("TZ", "EST5EDT", 1);
    tzset();

    time_t rawtime;
    struct tm *timeinfo;

    time(&rawtime);
    timeinfo = localtime(&rawtime);

    strftime(buffer, 32, format, timeinfo);
}

/**
 * @brief Converts a uint8_t array to its hexadecimal string representation.
 * @param uid       The input uint8_t array.
 * @param uid_len   The length of the input array.
 * @param uid_str   The output string buffer to store the hexadecimal representation.
 *                  It should have a size of at least 2*uid_len + 1.
 */
void uint_to_hexstr(const uint8_t *uid, size_t uid_len, char *uid_str) {
    // Ensure input pointers are not NULL
    if (!uid || !uid_str) {
        return;
    }

    for (size_t i = 0; i < uid_len; i++) {
        sprintf(uid_str + 2 * i, "%02X", uid[i]);
    }
    uid_str[2 * uid_len] = '\0';  // Null-terminate the resulting string
}

/**
 * @brief Checks if debounce time has passed since the last button release.
 * @param current_time The current time.
 * @param last_release The last release time.
 * @return 1 if debounce time has passed, 0 otherwise.
 */
int is_debounce_time_passed(struct timespec current_time, struct timespec last_release, int debounce_time) {
    long total_diff_nsec = (current_time.tv_sec - last_release.tv_sec) * 1000000000L 
                        + (current_time.tv_nsec - last_release.tv_nsec);

    long total_debounce_nsec = debounce_time * 1000000L;

    if (total_diff_nsec > total_debounce_nsec) {
        return 1;
    }

    return 0;
}