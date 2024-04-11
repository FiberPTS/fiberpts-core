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

void uint_to_hexstr(const uint8_t *uid, size_t uid_len, char *uid_str) {
    // Ensure input pointers are not NULL
    if (!uid || !uid_str) {
        return;
    }

    for (size_t i = 0; i < uid_len; i++) {
        sprintf(uid_str + 2 * i, "%02X", uid[i]);
    }
    uid_str[2 * uid_len] = '\0';  // Null-terminate the resulting string
}

void poll(char *uid_str, size_t buffer_size) {
    signal(SIGINT, stop_polling);

    // Define poll number and period for NFC device polling
    const uint8_t uiPollNr = 20;
    const uint8_t uiPeriod = 2;
    // Define modulation settings for polling
    const nfc_modulation nmModulations[5] = {
        {.nmt = NMT_ISO14443A, .nbr = NBR_106},
        {.nmt = NMT_ISO14443B, .nbr = NBR_106},
        {.nmt = NMT_FELICA, .nbr = NBR_212},
        {.nmt = NMT_FELICA, .nbr = NBR_424},
        {.nmt = NMT_JEWEL, .nbr = NBR_106},
    };
    const size_t szModulations = 5; // Number of modulations

    nfc_target nt; // NFC target structure
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

    // TODO: Make this a loop to poll indefinitely, so use passive polling
    // Start polling for NFC targets
    if ((res = nfc_initiator_poll_target(pnd, nmModulations, szModulations, uiPollNr, uiPeriod, &nt)) < 0)
    {
        nfc_perror(pnd, "nfc_initiator_poll_target");
        nfc_close(pnd);
        nfc_exit(context);
        exit(EXIT_FAILURE);
    }

    // Handle polling result
    if (res > 0)
    {
        nfc_close(pnd);
        nfc_exit(context);
        if (!uint_to_hexstr(nt.nti.nai.abtUid, nt.nti.nai.szUidLen, uid_str))
        {
            exit(EXIT_FAILURE);
        }
    }
    else
    {
        printf("No target found.\n");
    }

    // Wait for card removal
    printf("Waiting for card removing...");
    while (0 == nfc_initiator_target_is_present(pnd, NULL))
    {
    }
    nfc_perror(pnd, "nfc_initiator_target_is_present");
    printf("done.\n");

    // Cleanup
    nfc_close(pnd);
    nfc_exit(context);
}

int main(int argc, const char *argv[])
{
    signal(SIGINT, stop_polling);

    // Define poll number and period for NFC device polling
    const uint8_t uiPollNr = 20;
    const uint8_t uiPeriod = 2;
    // Define modulation settings for polling
    const nfc_modulation nmModulations[5] = {
        {.nmt = NMT_ISO14443A, .nbr = NBR_106},
        {.nmt = NMT_ISO14443B, .nbr = NBR_106},
        {.nmt = NMT_FELICA, .nbr = NBR_212},
        {.nmt = NMT_FELICA, .nbr = NBR_424},
        {.nmt = NMT_JEWEL, .nbr = NBR_106},
    };
    const size_t szModulations = 5; // Number of modulations

    nfc_target nt; // NFC target structure
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
    printf("NFC reader: %s opened\n", nfc_device_get_name(pnd));
    printf("NFC device will poll during %ld ms (%u pollings of %lu ms for %" PRIdPTR " modulations)\n", (unsigned long)uiPollNr * szModulations * uiPeriod * 150, uiPollNr, (unsigned long)uiPeriod * 150, szModulations);
    if ((res = nfc_initiator_poll_target(pnd, nmModulations, szModulations, uiPollNr, uiPeriod, &nt)) < 0)
    {
        nfc_perror(pnd, "nfc_initiator_poll_target");
        nfc_close(pnd);
        nfc_exit(context);
        exit(EXIT_FAILURE);
    }

    // Handle polling result
    if (res > 0)
    {
        printf("The following (NFC) ISO14443A tag was found:\n");
        printf("    ATQA (SENS_RES): ");
        print_hex(nt.nti.nai.abtAtqa, 2);
        printf("       UID (NFCID%c): ", (nt.nti.nai.abtUid[0] == 0x08 ? '3' : '1'));
        print_hex(nt.nti.nai.abtUid, nt.nti.nai.szUidLen);
        printf("      SAK (SEL_RES): ");
        print_hex(&nt.nti.nai.btSak, 1);
        if (nt.nti.nai.szAtsLen)
        {
            printf("          ATS (ATR): ");
            print_hex(nt.nti.nai.abtAts, nt.nti.nai.szAtsLen);
        }
    }
    else
    {
        printf("No target found.\n");
    }

    // Wait for card removal
    printf("Waiting for card removing...");
    while (0 == nfc_initiator_target_is_present(pnd, NULL))
    {
    }
    nfc_perror(pnd, "nfc_initiator_target_is_present");
    printf("done.\n");

    // Cleanup
    nfc_close(pnd);
    nfc_exit(context);
    exit(EXIT_SUCCESS);
}