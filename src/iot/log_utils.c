#include "log_utils.h"
#include "utils.h"
#include <time.h>
#include <stdlib.h>
#include <stdio.h>

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
