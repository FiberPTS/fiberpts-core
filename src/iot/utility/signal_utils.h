#ifndef SIGNAL_UTILS_H
#define SIGNAL_UTILS_H

#include <signal.h>

// Global signaling variables
extern volatile sig_atomic_t interrupted;
// Function pointer for cleanup operations
typedef void (*cleanup_function_t)(void);

// Enum to define the bitmask options for various signals
typedef enum {
    HANDLE_SIGINT  = 1 << 0,  // Represents the SIGINT signal (e.g., from Ctrl+C)
    HANDLE_SIGUSR1 = 1 << 1,  // Represents the SIGUSR1 signal
    HANDLE_SIGTERM = 1 << 2,  // Represents the SIGTERM signal
    // Add other signals as needed
} SignalOptions;

// Function prototypes
void handle_sigint(int sig);
void sleep_interruptible(int ms);
void handle_sigusr1(int sig);
int initialize_signal_handlers(int options, cleanup_function_t fn);

#endif // SIGNAL_UTILS_H