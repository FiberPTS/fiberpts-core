#include "log_utils.h"
#include "utils.h"
#include <time.h>
#include <stdlib.h>
#include <stdio.h>

// TODO: Fix logging (program_name)
// TODO: Find and remove libraries that are unnecessary

/**
 * @brief Prints a formatted log message with a timestamp and program name.
 * @param program_name The name of the program or module.
 * @param format The format string for the log message.
 * @param ... Additional arguments for the format string.
 */
void print_log(const char *program_name, const char *format, ...) {
    va_list argptr;
    va_start(argptr, format);

    char timestamp[32];
    get_current_time_in_est(timestamp, "%Y-%m-%d %H:%M:%S");

    if (format[0] == '\n') {
        printf("\n%s::%s::", timestamp, program_name);
        format++;
    } else {
        printf("%s::%s::", timestamp, program_name);
    }

    vprintf(format, argptr);

    va_end(argptr);
}

/**
 * @brief Prints an error log message with a timestamp, program name, and additional system error details.
 * @param program_name The name of the program or module.
 * @param format The format string for the log message.
 * @param ... Additional arguments for the format string.
 */
void perror_log(const char *program_name, const char *format, ...) {
    va_list argptr;
    va_start(argptr, format);

    char timestamp[32];
    get_current_time_in_est(timestamp, "%Y-%m-%d %H:%M:%S");

    fprintf(stderr, "%s::%s::", timestamp, program_name);
    vfprintf(stderr, format, argptr);

    perror("");

    va_end(argptr);
}

/**
 * @brief Prints a hexadecimal representation of the given data.
 * @param program_name The name of the program or module.
 * @param pbtData Pointer to the data.
 * @param szBytes Size of the data in bytes.
 */
void print_hex(const char *program_name, const uint8_t *pbtData, const size_t szBytes) {
    if (!pbtData || !program_name) {
        print_log(program_name, "Invalid input to print_hex");
        return;
    }

    // Ensure szBytes isn't too large to prevent potential stack overflow.
    if (szBytes > 1024) {  // Arbitrary limit, adjust as needed
        print_log(program_name, "Data too large to process in print_hex");
        return;
    }

    char message[szBytes * 3 + 1];  // 2 characters for hex + 1 for space
    char *current = message;

    for (size_t szPos = 0; szPos < szBytes; szPos++) {
        current += sprintf(current, "%02x ", pbtData[szPos]);
    }

    // Replace the last space with a newline
    if (szBytes > 0) {
        message[szBytes * 3 - 1] = '\n';
    }

    message[szBytes * 3] = '\0';  // Null-terminate the string
    print_log(program_name, message);
}