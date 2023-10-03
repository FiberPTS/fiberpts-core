#pragma once

char *get_machine_id();
void send_data_to_pipe(const char *data);
void get_current_time_in_est(char *buffer, const char *format);