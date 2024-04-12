// Last working compilation:
// sudo gcc -I/opt/libnfc-1.8.0/include -I/opt/libnfc-1.8.0 -o /opt/FiberPTS/src/nfc_reader/poll /opt/FiberPTS/src/nfc_reader/poll.c -L/opt/libnfc-1.8.0/utils -lnfc
#include <stdlib.h>
#include <err.h>
#include <inttypes.h>
#include <signal.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <nfc/nfc.h>
#include <nfc/nfc-types.h>
#include "utils/nfc-utils.h"

#define MAX_DEVICE_COUNT 16

static nfc_device *pnd = NULL;
static nfc_context *context;

// TODO: Need to compile this such that it can be called from python
// TODO: Fix the Makefile so that it not only compiles the linked files correctly,
// but also correctly cleans up the compiled files 
// (i.e. removes the .o files except for the libnfc ones)

// Function to handle the stop signal (SIGINT)
static void stop_polling(int sig)
{
    (void)sig; // Avoid unused variable warning
    if (pnd != NULL)
        nfc_abort_command(pnd); // Abort current NFC command
    else
    {
        nfc_exit(context);  // Exit NFC context
        exit(EXIT_FAILURE); // Exit program with failure status
    }
}

bool uint_to_hexstr(const uint8_t *uid, size_t uid_len, char *uid_str) {
    // Ensure input pointers are not NULL
    if (uid == NULL || uid_str == NULL) {
        return false;
    }

    printf("uid_len = %zu, uid_str address = %p\n", uid_len, (void*)uid_str);

    memset(uid_str, 0, 2 * uid_len + 1);

    for (size_t i = 0; i < uid_len; i++) {
        snprintf(uid_str + 2 * i, 3, "%02X", uid[i]);
    }
    uid_str[2 * uid_len] = '\0';  // Null-terminate the resulting string
    return true;
}

void poll(char *uid_str, size_t buffer_size) {
    signal(SIGINT, stop_polling);

    // Define modulation settings for polling
    const nfc_modulation nmMifare = {
        .nmt = NMT_ISO14443A,
        .nbr = NBR_106,
    };

    nfc_target nt; // NFC target structure
    nt.nti.nai.szUidLen = 0; // Initialize UID length to 0
    int res = 0;   // Result of NFC operations

    // Initialize libnfc context
    nfc_init(&context);
    if (context == NULL)
    {
        ERR("Unable to init libnfc (malloc)");
        exit(EXIT_FAILURE);
    }

    // Open NFC device
    pnd = nfc_open(context, NULL);
    if (pnd == NULL)
    {
        ERR("%s", "Unable to open NFC device.");
        nfc_exit(context);
        exit(EXIT_FAILURE);
    }

    // Initialize NFC device as initiator
    if (nfc_initiator_init(pnd) < 0)
    {
        nfc_perror(pnd, "nfc_initiator_init");
        nfc_close(pnd);
        nfc_exit(context);
        exit(EXIT_FAILURE);
    }

    // Start polling for NFC targets
    while ((res = nfc_initiator_select_passive_target(pnd, nmMifare, NULL, 0, &nt)) < 0)
    {
        sleep(0.1);
    }

    if (!uint_to_hexstr(nt.nti.nai.abtUid, nt.nti.nai.szUidLen, uid_str))
    {
        printf("Error converting UID to string\n");
        nfc_close(pnd);
        nfc_exit(context);
        exit(EXIT_FAILURE);
    }

    // Wait for card removal
    printf("Waiting for card removing...");
    // Invalid argument(s) is expected when no card was ever found during polling
    // This is due to the NULL argument indicating to look at the most recent target (which doesn't exist) 
    while (0 == nfc_initiator_target_is_present(pnd, NULL))
    {
    }
    nfc_perror(pnd, "nfc_initiator_target_is_present");
    printf("done.\n");

    // Cleanup
    nfc_close(pnd);
    nfc_exit(context);

}

void main(void)
{
    char uid_str[32];
    poll(uid_str, sizeof(uid_str));
    printf("UID: %s\n", uid_str);
}