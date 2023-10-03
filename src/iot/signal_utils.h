#ifndef SIGNAL_UTILS_H
#define SIGNAL_UTILS_H

#include <signal.h>

// Global signaling variables
extern volatile sig_atomic_t interrupted;

// Function prototypes
void handle_sigint(int sig);
void sleep_interruptible(int ms);
void handle_sigusr1(int sig);
void initialize_signal_handlers(void);

#endif // SIGNAL_UTILS_H