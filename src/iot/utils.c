#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

/**
 * @brief Retrieves the machine's unique ID.
 * @return A string containing the machine's ID or NULL on failure.
 */
char *get_machine_id() {
    FILE *file = fopen("/etc/machine-id", "r");
    if (file == NULL) {
        perror("Unable to open /etc/machine-id");
        return NULL;
    }

    char *machine_id = malloc(33);
    if (fgets(machine_id, 33, file) == NULL) {
        perror("Unable to read /etc/machine-id");
        fclose(file);
        free(machine_id);
        return NULL;
    }

    fclose(file);
    return machine_id;
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
