#pragma once
#include <stdarg.h>

void print_log(const char *program_name, const char *format, ...);
void perror_log(const char *program_name, const char *format, ...);
