#include <stdlib.h>
#include <err.h>
#include <inttypes.h>
#include <signal.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <unistd.h>
#include <nfc/nfc.h>
#include <nfc/nfc-types.h>
#include "utils/nfc-utils.h"

#define MAX_DEVICE_COUNT 16

static nfc_device *pnd = NULL;
static nfc_context *context;

/**
 * @brief the stop signal (SIGINT), aborting the current NFC command if a device is active,
 * or exiting the program otherwise.
 *
 * @param sig The signal number (unused).
 */
static void stop_polling(int sig)
{
    (void)sig; // Avoid unused variable warning
    if (pnd != NULL) {
        nfc_abort_command(pnd); // Abort current NFC command
    } else {
        nfc_exit(context);  // Exit NFC context
        exit(EXIT_FAILURE); // Exit program with failure status
    }
}

/**
 * @brief Converts a UID of an NFC tag from bytes to a hexadecimal string.
 *
 * @param uid Pointer to the byte array containing the UID.
 * @param uid_len The length of the UID byte array.
 * @param uid_str Pointer to the character array where the hexadecimal string will be stored.
 * @return True if conversion is successful, otherwise False.
 */
bool uint_to_hexstr(const uint8_t *uid, size_t uid_len, char *uid_str) {
    if (uid == NULL || uid_str == NULL) {
        return false;
    }

    memset(uid_str, 0, 2 * uid_len + 1);
    for (size_t i = 0; i < uid_len; i++) {
        snprintf(uid_str + 2 * i, 3, "%02X", uid[i]);
    }
    uid_str[2 * uid_len] = '\0';  // Null-terminate the resulting string
    return true;
}

/**
 * @brief Polls for NFC tags and writes the UID of the first detected tag into the provided buffer as a hexadecimal string.
 *
 * @param uid_str Pointer to the buffer where the UID string will be stored.
 * @param buffer_size The size of the provided buffer.
 */
void poll(char *uid_str, size_t buffer_size) {
    signal(SIGINT, stop_polling);

    const nfc_modulation nmMifare = {
        .nmt = NMT_ISO14443A,
        .nbr = NBR_106,
    };

    nfc_target nt; // NFC target structure
    nt.nti.nai.szUidLen = 0; // Initialize UID length to 0
    int res = 0;   // Result of NFC operations

    nfc_init(&context);
    if (context == NULL) {
        ERR("Unable to init libnfc (malloc)");
        exit(EXIT_FAILURE);
    }

    pnd = nfc_open(context, NULL);
    if (pnd == NULL) {
        ERR("Unable to open NFC device.");
        nfc_exit(context);
        exit(EXIT_FAILURE);
    }

    if (nfc_initiator_init(pnd) < 0) {
        nfc_perror(pnd, "nfc_initiator_init");
        nfc_close(pnd);
        nfc_exit(context);
        exit(EXIT_FAILURE);
    }

    while ((res = nfc_initiator_select_passive_target(pnd, nmMifare, NULL, 0, &nt)) < 0) {
        sleep(0.25);
    }

    nfc_close(pnd);
    nfc_exit(context);

    if (nt.nti.nai.szUidLen > buffer_size) {
        printf("UID buffer too small\n");
        exit(EXIT_FAILURE);
    }

    if (!uint_to_hexstr(nt.nti.nai.abtUid, nt.nti.nai.szUidLen, uid_str)) {
        printf("Error converting UID to string\n");
        exit(EXIT_FAILURE);
    }
}

/**
 * @brief Main function that initializes a buffer for the UID string, calls poll to fill it,
 * and prints the UID string.
 */
int main(void) {
    char uid_str[32];
    poll(uid_str, sizeof(uid_str));
    printf("UID: %s\n", uid_str);
    return 0;
}
