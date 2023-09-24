#include <stdio.h>
#include <stdlib.h>
#include <nfc/nfc.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <ctype.h>
#include <time.h>
#include <stdarg.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>

const char *fifo_path = "/tmp/screenPipe";

void print_log(const char *format, ...) {
    /**
     * Function: print_log
     * -------------------
     * Logs messages with a timestamp.
     *
     * @param format: A format string for the message to be logged.
     * @param ...: Variable arguments for the format string.
     */
    va_list argptr;
    va_start(argptr, format);
    // Set timezone to EST
    setenv("TZ", "EST5EDT", 1);
    tzset();

    time_t rawtime;
    struct tm * timeinfo;

    time (&rawtime);
    timeinfo = localtime(&rawtime);
    
    char buffer[80];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);

    // check if the first character of the format string is a newline
    if (format[0] == '\n') {
        printf("\n%s::read_ultralight::", buffer);  // add newline before the timestamp
        format++;  // move the pointer to skip the first character
    } else {
        printf("%s::read_ultralight::", buffer);
    }
    vprintf(format, argptr);

    va_end(argptr);
}

void perror_log(const char *format, ...) {
    /**
     * Function: perror_log
     * --------------------
     * Logs error messages with a timestamp.
     *
     * @param format: A format string for the error message to be logged.
     * @param ...: Variable arguments for the format string.
     */
    va_list argptr;
    va_start(argptr, format);
    // Set timezone to EST
    setenv("TZ", "EST5EDT", 1);
    tzset();

    time_t rawtime;
    struct tm * timeinfo;

    time (&rawtime);
    timeinfo = localtime(&rawtime);

    char buffer[80];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);
    fprintf(stderr, "%s::read_ultralight::", buffer);
    vfprintf(stderr, format, argptr);

    perror("");

    va_end(argptr);
}

char* get_machine_id() {
    /**
     * Function: get_machine_id
     * ------------------------
     * Reads the machine ID from the system.
     *
     * Returns:
     * - A pointer to the machine ID string.
     * - NULL on failure.
     */
    FILE* file = fopen("/etc/machine-id", "r");
    if (file == NULL) {
        perror_log("Unable to open /etc/machine-id");
        return NULL;
    }

    char* machine_id = malloc(33); // the machine ID is a 32-character string, plus '\0' at the end
    if (fgets(machine_id, 33, file) == NULL) {
        perror_log("Unable to read /etc/machine-id");
        fclose(file);
        return NULL;
    }

    fclose(file);

    return machine_id;
}

void print_hex(const uint8_t *pbtData, const size_t szBytes) {
    /**
     * Function: print_hex
     * -------------------
     * Prints a byte array as a series of hexadecimal values.
     *
     * @param pbtData: Pointer to the byte array.
     * @param szBytes: Number of bytes in the array.
     */
    char message[szBytes*3 + 1]; // Create a string that can hold all hexadecimal values and spaces
    char *current = message; // Pointer to current position in the message string

    for (size_t szPos = 0; szPos < szBytes; szPos++) {
        current += sprintf(current, "%02x ", pbtData[szPos]); // Write the hex value to the string and update the current pointer
    }

    // Replace the last space with a newline
    message[szBytes*3 - 1] = '\n';
    message[szBytes*3] = '\0';  // Add a null terminator at the end
    print_log(message);
}

void send_data_to_pipe(const char * data) {
    /**
     * Function: send_data_to_pipe
     * ---------------------------
     * Sends data to a named pipe.
     *
     * @param data: The data string to send.
     */
    int fd;
    fd = open(fifo_path, O_WRONLY);
    write(fd, data, strlen(data) + 1);
    close(fd);
}

int main(int argc, const char *argv[]) {

    // Create a named pipe for inter-process communication.
    mkfifo(fifo_path, 0666);

    nfc_device *pnd;
    nfc_target nt;
    nfc_context *context;
    nfc_init(&context);

    if (context == NULL) {
    print_log("Unable to init libnfc (malloc)\n");
    exit(EXIT_FAILURE);
    }

    pnd = nfc_open(context, NULL);

    if (pnd == NULL) {
    print_log("%s", "Unable to open NFC device.");
    exit(EXIT_FAILURE);
    }

    if (nfc_initiator_init(pnd) < 0) {
    nfc_perror(pnd, "nfc_initiator_init");
    exit(EXIT_FAILURE);
    }

    print_log("NFC reader: %s opened\n", nfc_device_get_name(pnd));

    const nfc_modulation nmMifare = {
      .nmt = NMT_ISO14443A,
      .nbr = NBR_106,
    };

    uint8_t last_uid[10];

    bool same_card = false;

    // Main loop for detecting NFC tags and sending data to pipe
    while(1){

        if (nfc_initiator_select_passive_target(pnd, nmMifare, NULL, 0, &nt) > 0) {
            // NFC tag found
            print_log("The following (NFC) ISO14443A tag was found:\n");
            print_log("UID (NFCID%c): \n", (nt.nti.nai.abtUid[0] == 0x08 ? '3' : '1'));
            print_hex(nt.nti.nai.abtUid, nt.nti.nai.szUidLen);

            if (memcmp(nt.nti.nai.abtUid, last_uid, nt.nti.nai.szUidLen) == 0 && same_card) {
                // The same card is still present, don't read it again
                print_log("Same card found!\n");
                usleep(10*1000);
                continue;
            }

            memcpy(last_uid, nt.nti.nai.abtUid, nt.nti.nai.szUidLen);
            same_card = true;
            char uid_str[2*nt.nti.nai.szUidLen + 1];

            for (int i = 0; i < nt.nti.nai.szUidLen; i++) {
                sprintf(uid_str + 2 * i, "%02X", last_uid[i]);
            }

            char data_to_send_buffer[24 + sizeof(uid_str)];

            strcpy(data_to_send_buffer, "read_ultralight.c-program-");
            strcat(data_to_send_buffer, uid_str);

            send_data_to_pipe((const char *) data_to_send_buffer);

            print_log("read_ultralight::NFC Read");

            // Wait for 10ms before the next loop iteration
            usleep(10*1000); // usleep function takes microseconds, so multiply by 1000
        } else if(same_card) {

            // No new card was detected, wait for 100ms
            usleep(100*1000);

            // If no new card is detected after 100ms, set same_card to false
            if (nfc_initiator_select_passive_target(pnd, nmMifare, NULL, 0, &nt) <= 0) {
                print_log("Tag was released\n");
                same_card = false;
            }
        } else {

            // No card was detected, wait for 10ms
            usleep(10*1000);

            print_log("No tag detected\n");
        }
    }

    nfc_close(pnd);
    nfc_exit(context);
    exit(EXIT_SUCCESS);
}
