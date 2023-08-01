#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <gpiod.h>

#define BUTTON_LINE_NUMBER 98
#define DEBOUNCE_TIME 50 // debounce time in milliseconds

// Time of the last button press
static struct timespec last_press_time;

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

int initialize_gpio(void) {
    chip = gpiod_chip_open_by_name("gpiochip1");
    if (!chip) {
        perror("Open chip failed\n");
        return 1;
    }

    button_line = gpiod_chip_get_line(chip, BUTTON_LINE_NUMBER);
    if (!button_line) {
        perror("Get line failed\n");
        gpiod_chip_close(chip);
        return 1;
    }
    /*
    int ret = gpiod_line_request_rising_edge_events(button_line, "button");
    if (ret < 0) {
        perror("Request both edges events failed");
        gpiod_chip_close(chip);
        return 1;
    }
    */
    int ret = gpiod_line_request_input(button_line, "button");
    if (ret < 0) {
        perror("Request line as input failed");
        gpiod_chip_close(chip);
        return 1;
    }

    return 0;
}

void cleanup_gpio(void) {
    gpiod_line_release(button_line);
    gpiod_chip_close(chip);
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
	    perror("Read line value failed");
	} else if (value == 1) {
	    // Check if enough time has passed since the last press
	    if ((current_time.tv_sec > last_press_time.tv_sec) ||
	        (current_time.tv_sec == last_press_time.tv_sec && current_time.tv_nsec > last_press_time.tv_nsec + DEBOUNCE_TIME * 1000000)) {
	        // Enough time has passed, handle the button press
	        //handle_button_press();
	        printf("Button Pressed\n");
		// Update the time of the last press
	        last_press_time = current_time;
	    }
	}
    }
    cleanup_gpio();
    return 0;
}
