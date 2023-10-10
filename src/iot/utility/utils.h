#pragma once
#include <stddef.h>
#include <stdint.h>
#include <time.h>

// TODO: Find and remove libraries that are unnecessary

char *get_device_id();
void send_data_to_pipe(const char *data, const char *fifo_path);
void get_current_time_in_est(char *buffer, const char *format);
void uint_to_hexstr(const uint8_t *uid, size_t uid_len, char *uid_str);
int is_debounce_time_passed(struct timespec current_time, struct timespec last_release, int debounce_time);