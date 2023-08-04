#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <gpiod.h>
#include <stdarg.h>
#include <curl/curl.h>
#include <json-c/json.h>

#define BUTTON_LINE_NUMBER 88
//#define BUTTON_LINE_NUMBER 96
#define DEBOUNCE_TIME 1000 // debounce time in milliseconds

// Time of the last button press
static struct timespec last_release_time;
// Whether the button is currently pressed
static int button_pressed = 0;

struct gpiod_chip *chip;
struct gpiod_line *button_line;

volatile sig_atomic_t interrupted = 0;

void cleanup_gpio(void);

// This function will be called when SIGINT is sent to the program (Ctrl+C)
void handle_sigint(int sig) {
    interrupted = 1;
    cleanup_gpio();
    exit(0);
}

// The function that logs messages with timestamp
void print_log(const char *format, ...) {
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
        printf("\n%s: ", buffer);  // add newline before the timestamp
        format++;  // move the pointer to skip the first character
    } else {
        printf("%s: ", buffer);
    }
    vprintf(format, argptr);

    va_end(argptr);
}

// The function that logs error messages with timestamp
void perror_log(const char *format, ...) {
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
    fprintf(stderr, "%s: ", buffer);
    vfprintf(stderr, format, argptr);

    perror("");

    va_end(argptr);
}

// Function to send a signal to the read_mifare program
void send_signal_to_read_mifare(void) {
    FILE *file = fopen("/var/run/read_ultralight.pid", "r");
    if (!file) {
        perror_log("Failed to open PID file");
        return;
    }

    pid_t read_ultralight_pid;
    if (fscanf(file, "%d", &read_ultralight_pid) != 1) {
        perror_log("Failed to read PID from file");
        fclose(file);
        return;
    }

    fclose(file);

    // Send SIGUSR1 to the read_ultralight program
    if (kill(read_ultralight_pid, SIGUSR1) == -1) {
        perror_log("Failed to send signal");
    }
}

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

void cleanup_gpio(void) {
    gpiod_line_release(button_line);
    gpiod_chip_close(chip);
}

void send_post_request(char *url, const char *payload) {
    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url);

        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload);

        res = curl_easy_perform(curl);

        if(res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        }
        curl_easy_cleanup(curl);
    }
}

char* get_machine_id() {
    FILE* file = fopen("/etc/machine-id", "r");
    if (file == NULL) {
        perror_log("Unable to open /etc/machine-id");
        return NULL;
    }

    char* machine_id = malloc(33); // the machine ID is a 32-character string, plus '\0' at the end
    if (fgets(machine_id, 33, file) == NULL) {
        perror_log("Unable to read /etc/machine-id");
        fclose(file);
        return NULL;
    }

    fclose(file);

    return machine_id;
}

void handle_button_press() {
    char url[] = "https://hooks.airtable.com/workflows/v1/genericWebhook/appZUSMwDABUaufib/wflBeyntdIrWMVuQG/wtrYOlc9Mgwie9Ui9";
    // Get machine ID
    char* machine_id = get_machine_id();
    if (machine_id == NULL) {
        // handle error
        print_log("Failed Sending: Could not find Machine ID\n");
        return;
    }
    json_object * jobj = json_object_new_object();
    json_object *jstring = json_object_new_string(machine_id);
    json_object_object_add(jobj,"Machine ID", jstring);
    const char* json_payload = json_object_to_json_string_ext(jobj, JSON_C_TO_STRING_PRETTY);
    send_post_request(url, json_payload);
    print_log("\nSent POST request.\n");

    // Free allocated memory
    //free(combined_payload);
    free(machine_id);
    json_object_put(jobj); // free json object
}

int main(void) {
    // Register the function to call on SIGINT
    signal(SIGINT, handle_sigint);

    if (initialize_gpio() != 0) {
        return 1;
    }

    while (!interrupted) {
        struct timespec current_time;
        clock_gettime(CLOCK_MONOTONIC, &current_time);
        int value = gpiod_line_get_value(button_line);
        if (value < 0) {
            perror_log("Read line value failed");
        } else if (value == 0) {
            // Button is currently pressed
            if (!button_pressed) {
                // This is a new button press
                // Check if enough time has passed since the last release
                if ((current_time.tv_sec > last_release_time.tv_sec) ||
                    (current_time.tv_sec == last_release_time.tv_sec && current_time.tv_nsec > last_release_time.tv_nsec + DEBOUNCE_TIME * 1000000)) {
                    // Enough time has passed, handle the button press
                    handle_button_press();
                    button_pressed = 1;
                    send_signal_to_read_mifare();
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