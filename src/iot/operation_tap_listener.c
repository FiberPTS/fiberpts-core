#include <fcntl.h>
#include <gpiod.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define BUTTON_LINE_NUMBER 80  // Black on GND and Red on GPIO
#define DEBOUNCE_TIME 1000     // debounce time in milliseconds
#define VOLTAGE_VALUE 1        // Voltage value corresponding to button press

static struct timespec last_release_time;  // Time of the last button press
static int button_pressed = 0;             // Flag for whether button is pressed

const char *fifo_path = "/tmp/screenPipe";  // Pipe file path

struct gpiod_chip *chip;         // GPIO chip struct
struct gpiod_line *button_line;  // GPIO line struct

// Flag checking for whether the program was interrupted
volatile sig_atomic_t interrupted = 0;

void cleanup_gpio(void);

/**
 * @brief Signal handler for SIGINT (For instance, when Ctrl+C occurs).
 * @param sig The signal number
 */
void handle_sigint(int sig) {
  interrupted = 1;
  cleanup_gpio();
  exit(0);
}

/**
 * @brief Logs messages with a timestamp.
 * @param format The format string for the log message.
 * @param ... Variable arguments for the format string.
 */
void print_log(const char *format, ...) {
  va_list argptr;
  va_start(argptr, format);
  // Set timezone to EST
  setenv("TZ", "EST5EDT", 1);
  tzset();

  time_t rawtime;
  struct tm *timeinfo;

  time(&rawtime);
  timeinfo = localtime(&rawtime);

  char buffer[80];
  strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);

  if (format[0] == '\n') {
    printf("\n%s::button_listener::", buffer);
    format++;
  } else {
    printf("%s::button_listener::", buffer);
  }
  vprintf(format, argptr);

  va_end(argptr);
}

/**
 * @brief Logs error messages with a timestamp.
 * @param format The format string for the error message.
 * @param ... Variable arguments for the format string.
 */
void perror_log(const char *format, ...) {
  va_list argptr;
  va_start(argptr, format);

  // Set timezone to EST
  setenv("TZ", "EST5EDT", 1);
  tzset();

  time_t rawtime;
  struct tm *timeinfo;

  time(&rawtime);
  timeinfo = localtime(&rawtime);

  char buffer[80];
  strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);
  fprintf(stderr, "%s::button_listener::", buffer);
  vfprintf(stderr, format, argptr);

  perror("");

  va_end(argptr);
}

/**
 * @brief Initializes GPIO for button input.
 * @return 0 on success, 1 on failure.
 */
int initialize_gpio(void) {
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

/**
 * @brief Releases the GPIO resources.
 */
void cleanup_gpio(void) {
  gpiod_line_release(button_line);
  gpiod_chip_close(chip);
}

/**
 * @brief Retrieves the machine's unique ID.
 * @return A string containing the machine's ID or NULL on failure.
 */
char *get_machine_id() {
  FILE *file = fopen("/etc/machine-id", "r");
  if (file == NULL) {
    perror_log("Unable to open /etc/machine-id");
    return NULL;
  }

  char *machine_id = malloc(33);
  if (fgets(machine_id, 33, file) == NULL) {
    perror_log("Unable to read /etc/machine-id");
    fclose(file);
    return NULL;
  }

  fclose(file);

  return machine_id;
}

/**
 * @brief Sends data to a program using a named pipe.
 * @param data The data to send.
 */
void send_data_to_pipe(const char *data) {
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
        // Convert DEBOUNCE_TIME to seconds and nanoseconds components
        long debounce_sec = DEBOUNCE_TIME / 1000;
        long debounce_nsec = (DEBOUNCE_TIME % 1000) * 1000000;

        // Check if the difference in seconds exceeds the debounce
        // seconds
        bool sec_condition =
            current_time.tv_sec > last_release_time.tv_sec + debounce_sec;

        // Check if the seconds are equal and the difference in
        // nanoseconds exceeds the debounce nanoseconds
        bool nsec_condition =
            (current_time.tv_sec == last_release_time.tv_sec) &&
            (current_time.tv_nsec > last_release_time.tv_nsec + debounce_nsec);

        // Check if enough time has passed since the last release
        if (sec_condition || nsec_condition) {
          button_pressed = 1;
          const char *data_to_send = "button_listener.c-program-Button Pressed";
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