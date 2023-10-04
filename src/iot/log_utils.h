#pragma once
#include <stdarg.h>
#include <stdint.h>
#include <stddef.h>

void print_log(const char *program_name, const char *format, ...);
void perror_log(const char *program_name, const char *format, ...);
void print_hex(const char *program_name, const uint8_t *pbtData, const size_t szBytes);
