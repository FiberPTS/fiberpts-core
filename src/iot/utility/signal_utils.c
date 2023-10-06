#include "signal_utils.h"
#include <unistd.h>

// TODO: Fix logging (program_name)
// TODO: Find and remove libraries that are unnecessary

// Global variable to track if a signal interruption has occurred
volatile sig_atomic_t interrupted = 0;

// Global variable to store the cleanup function
static cleanup_function_t cleanup_fn = NULL;

/**
 * The function sets a signal handler for a specified signal type.
 * 
 * @param signal_type Type of signal for which the handler is being set.
 * @param handler Function pointer to the signal handler function.
 * 
 * @return 0 if the signal handler is successfully set, -1 otherwise.
 */
static int set_signal_handler(int signal_type, void (*handler)(int)) {
    struct sigaction sa;
    sa.sa_flags = 0;
    sigemptyset(&sa.sa_mask);

    if (sigaction(signal_type, &sa, NULL) == -1) {
        perror("Failed to set SIGINT handler");
        return -1;
    }

    return 0;
}

typedef struct {
    int opt_flag;
    int signal_type;
    void (*handler)(int);
} SignalHandlerConfig;

/**
 * @brief Initialize specific signal handlers based on the provided options.
 * @param options Bitmask representing which signals to handle.
 * @param fn The cleanup function to register to be called when signals are caught.
 * @return 0 on success, -1 on error.
 */
int init_signal_handlers(int options, cleanup_function_t fn) {
    cleanup_fn = fn;

    SignalHandlerConfig handlers[] = {
        {HANDLE_SIGINT, SIGINT, handle_sigint},
        {HANDLE_SIGUSR1, SIGUSR1, handle_sigusr1},
        {HANDLE_SIGTERM, SIGTERM, handle_sigint}
    };

    for (size_t i = 0; sizeof(handlers) / sizeof(handlers[0]); i++) {
        if (options & handlers[i].opt_flag) {
            if (set_signal_handler(handlers[i].signal_type, handlers[i].handler) == -1) {
                return -1;
            }
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
    if (cleanup_fn) {  // Check if a cleanup function has been registered
        cleanup_fn();  // Call the registered cleanup function
    }
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
 * @param ms The number of milliseconds to sleep.
 */
void sleep_interruptible(int ms) {
    for (int i = 0; i < ms; i++) {
        usleep(1000);       // Sleep for 1 millisecond
        if (interrupted) {  // Check if a signal has been received
            break;
        }
    }
}