// Standard library headers
// TODO: Find and remove libraries that are unnecessary
// TODO: Fix logging (program_name)
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>
#include <nfc/nfc.h>

// Local project headers
#include "utility/log_utils.h"
#include "utility/signal_utils.h"
#include "utility/utils.h"

// Constants
#define DEBOUNCE_TIME 1000 // Debounce time in milliseconds

// File paths and names
const char *FIFO_PATH = "/tmp/tap_event_handler";
const char *PROGRAM_NAME = "nfc_tap_listener.c";

// NFC Configurations
nfc_device *pnd;
nfc_context *context;
nfc_target nt;
const nfc_modulation nmMifare = {
    .nmt = NMT_ISO14443A,
    .nbr = NBR_106,
};

// State variables
static struct timespec last_release_time; // Time of the last NFC tap

/**
 * @brief Cleanup function to release NFC resources.
 */
void cleanup() {
    nfc_close(pnd);
    nfc_exit(context);
}

int main(void) {
    // Initialize NFC Reader and its associated variables
    nfc_init(&context);
    if (!context) {
        // print_log(PROGRAM_NAME, "Unable to init libnfc (malloc)\n");
        exit(EXIT_FAILURE);
    }
    pnd = nfc_open(context, NULL);
    if (!pnd) {
        // print_log(PROGRAM_NAME, "Unable to open NFC device.");
        exit(EXIT_FAILURE);
    }
    if (nfc_initiator_init(pnd) < 0) {
        nfc_perror(pnd, "nfc_initiator_init");
        exit(EXIT_FAILURE);
    }
    // print_log(PROGRAM_NAME, "NFC Reader: %s opened\n", nfc_device_get_name(pnd));

    // Signal handling initialization
    if (initialize_signal_handlers(HANDLE_SIGINT | HANDLE_SIGUSR1 | HANDLE_SIGTERM, cleanup) == -1) {
        perror_log(PROGRAM_NAME, "Error initializing signal handlers: ");
        return 1;
    }

    // Initialize the named pipe for IPC
    if (mkfifo(FIFO_PATH, 0666) == -1 && errno != EEXIST) {
        perror_log(PROGRAM_NAME, "Error creating named pipe: ");
        return 1;
    }

    uint8_t last_uid[10];
    bool same_tag = false;
    bool tag_found = false;
    // Sets the last release time
    clock_gettime(CLOCK_MONOTONIC, &last_release_time);

    struct timespec current_time;

    while (!interrupted) {
        clock_gettime(CLOCK_MONOTONIC, &current_time);

        // Check for NFC tag presence
        if (nfc_initiator_select_passive_target(pnd, nmMifare, NULL, 0, &nt) > 0) {
            tag_found = true;

            // Display tag information
            // print_log(PROGRAM_NAME, "The following (NFC) ISO14443A tag was found:\n");
            // print_log(PROGRAM_NAME, "UID (NFCID%c): \n", (nt.nti.nai.abtUid[0] == 0x08 ? '3' : '1'));
            // print_hex(PROGRAM_NAME, nt.nti.nai.abtUid, nt.nti.nai.szUidLen);

            // Handle debounce time and check for the same tag
            if (!is_debounce_time_passed(current_time, last_release_time, DEBOUNCE_TIME)) {
                last_release_time = current_time;
                continue;
            }
            if (memcmp(nt.nti.nai.abtUid, last_uid, nt.nti.nai.szUidLen) == 0) {
                same_tag = true;
                // print_log(PROGRAM_NAME, "Same card found!\n");
                continue;
            } else {
                same_tag = false;
                memcpy(last_uid, nt.nti.nai.abtUid, nt.nti.nai.szUidLen);
            }
        } else {
            tag_found = false;
        }
        // TODO: Design choice of whether we should register the same tag in a row.
        // Process found tag
        if (tag_found) {
            char uid_str[2 * nt.nti.nai.szUidLen + 1];
            uint_to_hexstr(last_uid, nt.nti.nai.szUidLen, uid_str);

            char timestamp[32];
            get_current_time_in_est(timestamp, "%Y-%m-%d %H:%M:%S");

            char data_to_send[strlen(PROGRAM_NAME) + strlen(uid_str) + strlen(timestamp) + 5];  // 5 for "::" and null-terminator
            sn// printf(data_to_send, sizeof(data_to_send), "%s::%s::%s", PROGRAM_NAME, uid_str, timestamp);

            send_data_to_pipe(data_to_send, FIFO_PATH);
            // print_log(PROGRAM_NAME, "Registered NFC Tap");
        } else if (!same_tag) {
            // print_log(PROGRAM_NAME, "No tag detected");
        }
        sleep_interruptible(100);
    }
    cleanup();
    return 0;
}