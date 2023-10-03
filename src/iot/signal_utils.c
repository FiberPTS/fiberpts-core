#include "signal_utils.h"
#include <unistd.h>

// Global variable to track if a signal interruption has occurred
volatile sig_atomic_t interrupted = 0;

// Enum to define the bitmask options for various signals
typedef enum {
    HANDLE_SIGINT  = 1 << 0,  // Represents the SIGINT signal (e.g., from Ctrl+C)
    HANDLE_SIGUSR1 = 1 << 1,  // Represents the SIGUSR1 signal
    // Add other signals as needed
} SignalOptions;

/**
 * @brief Initialize specific signal handlers based on the provided options.
 * @param options Bitmask representing which signals to handle.
 * @return 0 on success, -1 on error.
 */
int initialize_signal_handlers(int options) {
    if (options & HANDLE_SIGINT) {
        if (signal(SIGINT, handle_sigint) == SIG_ERR) {
            perror("Failed to set SIGINT handler");
            return -1;
        }
    }
    if (options & HANDLE_SIGUSR1) {
        if (signal(SIGUSR1, handle_sigusr1) == SIG_ERR) {
            perror("Failed to set SIGUSR1 handler");
            return -1;
        }
    }
    return 0;
}

/**
 * @brief Signal handler for SIGINT (e.g., from Ctrl+C).
 * Sets the interrupted flag, cleans up GPIO, and exits the program.
 * @param sig The signal number. Expected to be SIGINT.
 */
void handle_sigint(int sig) {
    interrupted = 1;
    cleanup_gpio(); // This should call the specific function in the script inluding signal_utils.h
    exit(0);
}

/**
 * @brief Signal handler for SIGUSR1.
 * Currently does nothing but can be customized as needed.
 * @param sig The signal number. Expected to be SIGUSR1.
 */
void handle_sigusr1(int sig) {
    (void)sig; // To suppress unused parameter warning
    // Add the code to handle SIGUSR1 here if needed
}

/**
 * @brief Sleeps for a specified number of milliseconds, but can be interrupted early if the interrupted flag is set.
 * @param sec The number of seconds to sleep.
 */
void sleep_interruptible(int sec) {
    for (int i = 0; i < sec; i++) {
        usleep(1000);       // Sleep for 1ms
        if (interrupted) {  // Check if a signal has been received
            break;
        }
    }
}