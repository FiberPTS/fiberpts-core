#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <gpiod.h>
#include <stdarg.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>

#define BUTTON_LINE_NUMBER 80 // Black on GND and Red on GPIO
#define DEBOUNCE_TIME 1000 // debounce time in milliseconds
#define VOLTAGE_VALUE 1 // Voltage value corresponding to a button press being "on"

static struct timespec last_release_time; // Time of the last button press
static int button_pressed = 0; // Flag for whether button is pressed

const char *fifo_path = "/tmp/screenPipe"; // Pipe file path

struct gpiod_chip *chip; // GPIO chip struct
struct gpiod_line *button_line; // GPIO line struct

volatile sig_atomic_t interrupted = 0; // Flag checking for whether the program was interrupted.

void cleanup_gpio(void);

void handle_sigint(int sig) {
    /**
     * Function: handle_sigint
     * -----------------------
     * Signal handler for SIGINT (For instance, when Ctrl+C occurs).
     *
     * Parameters:
     *   sig: The signal number.
     *
     * Returns:
     *   void
     */
    interrupted = 1;
    cleanup_gpio();
    exit(0);
}

void print_log(const char *format, ...) {
    /**
     * Function: print_log
     * -------------------
     * Logs messages with a timestamp.
     *
     * Parameters:
     *   format: The format string for the log message.
     *   ...: Variable arguments for the format string.
     *
     * Returns:
     *   void
     */
    va_list argptr;
    va_start(argptr, format);
    // Set timezone to EST
    setenv("TZ", "EST5EDT", 1);
    tzset();

    time_t rawtime;
    struct tm * timeinfo;

    time (&rawtime);
    timeinfo = localtime(&rawtime);

    char buffer[80];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);

    // check if the first character of the format string is a newline
    if (format[0] == '\n') {
        printf("\n%s::button_listener::", buffer);  // add newline before the timestamp
        format++;  // move the pointer to skip the first character
    } else {
        printf("%s::button_listener::", buffer);
    }
    vprintf(format, argptr);

    va_end(argptr);
}

void perror_log(const char *format, ...) {
    /**
     * Function: perror_log
     * --------------------
     * Logs error messages with a timestamp.
     *
     * Parameters:
     *   format: The format string for the error message.
     *   ...: Variable arguments for the format string.
     *
     * Returns:
     *   void
     */
    va_list argptr;
    va_start(argptr, format);
    // Set timezone to EST
    setenv("TZ", "EST5EDT", 1);
    tzset();

    time_t rawtime;
    struct tm * timeinfo;

    time (&rawtime);
    timeinfo = localtime(&rawtime);

    char buffer[80];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);
    fprintf(stderr, "%s::button_listener::", buffer);
    vfprintf(stderr, format, argptr);

    perror("");

    va_end(argptr);
}

int initialize_gpio(void) {
    /**
     * Function: initialize_gpio
     * -------------------------
     * Initializes GPIO for button input.
     *
     * Returns:
     *   0 on success, 1 on failure.
     */
    chip = gpiod_chip_open_by_name("gpiochip1");
    if (!chip) {
        perror_log("Open chip failed");
        return 1;
    }

    button_line = gpiod_chip_get_line(chip, BUTTON_LINE_NUMBER);
    if (!button_line) {
        perror_log("Get line failed");
        gpiod_chip_close(chip);
        return 1;
    }


    int ret = gpiod_line_request_input(button_line, "button");
    if (ret < 0) {
        perror_log("Request line as input failed");
        gpiod_chip_close(chip);
        return 1;
    }

    return 0;
}

void cleanup_gpio(void) {
    /**
     * Function: cleanup_gpio
     * ----------------------
     * Releases the GPIO resources.
     *
     * Returns:
     *   void
     */
    gpiod_line_release(button_line);
    gpiod_chip_close(chip);
}

char* get_machine_id() {
    /**
     * Function: get_machine_id
     * ------------------------
     * Retrieves the machine's unique ID.
     *
     * Returns:
     *   A string containing the machine's ID or NULL on failure.
     */
    FILE* file = fopen("/etc/machine-id", "r");
    if (file == NULL) {
        perror_log("Unable to open /etc/machine-id");
        return NULL;
    }

    char* machine_id = malloc(33); // The machine ID is a 32-character string, plus '\0' at the end
    if (fgets(machine_id, 33, file) == NULL) {
        perror_log("Unable to read /etc/machine-id");
        fclose(file);
        return NULL;
    }

    fclose(file);

    return machine_id;
}

void send_data_to_pipe(const char * data) {
    /**
     * Function: send_data_to_pipe
     * -----------------------------
     * Sends data to a program using a named pipe.
     *
     * Parameters:
     *   data: The data to send.
     *
     * Returns:
     *   void
     */
    int fd;
    fd = open(fifo_path, O_WRONLY);
    write(fd, data, strlen(data) + 1);
    close(fd);
}

int main(void) {
    // Register the function to call on SIGINT
    signal(SIGINT, handle_sigint);

    // Initialize GPIO.
    if (initialize_gpio() != 0) {
        return 1;
    }

    // Create a named pipe for inter-process communication.
    mkfifo(fifo_path, 0666);

    // Main loop to monitor the button state.
    while (!interrupted) {
        struct timespec current_time;
        clock_gettime(CLOCK_MONOTONIC, &current_time);
        int value = gpiod_line_get_value(button_line);
        // Check the button state and handle press/release events.
        // Implement debounce logic to avoid false triggers.
        if (value < 0) {
            perror_log("Read line value failed");
        } else if (value == VOLTAGE_VALUE) {
            // Button is currently pressed
            if (!button_pressed) {
                // This is a new button press
                // Check if enough time has passed since the last release
                if ((current_time.tv_sec > last_release_time.tv_sec + DEBOUNCE_TIME / 1000) ||
                    (current_time.tv_sec == last_release_time.tv_sec && current_time.tv_nsec > last_release_time.tv_nsec + DEBOUNCE_TIME * 1000000)) {
                    // Enough time has passed, handle the button press
                    button_pressed = 1;
                    const char * data_to_send = "button_listener.c-program-Button Pressed";
                    send_data_to_pipe(data_to_send);
                    print_log("Button Pressed\n");
                } else {
                    button_pressed = 1;
                    last_release_time = current_time;
                }
            }
        } else {
            // Button is not currently pressed
            if (button_pressed) {
                // Button was just released
                button_pressed = 0;
                last_release_time = current_time;
            }
        }
    }
    cleanup_gpio();
    return 0;
}