#include <stdio.h>
#include <stdlib.h>
#include <nfc/nfc.h>
#include <unistd.h>
#include <string.h>
#include <curl/curl.h>
#include <json-c/json.h>
#include <gpiod.h>
#include <signal.h>
#include <ctype.h>
#include <time.h>
#include <stdarg.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>

#define CHIP "gpiochip1"
#define LED_R_LINE_NUMBER 93
#define LED_Y_LINE_NUMBER 94
#define LED_G_LINE_NUMBER 79

struct gpiod_chip *chip;
struct gpiod_line *red_line, *yellow_line, *green_line;

const char *fifo_path = "/tmp/screenPipe";

// The function that logs messages with timestamp
void print_log(const char *format, ...) {
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
        printf("\n%s: ", buffer);  // add newline before the timestamp
        format++;  // move the pointer to skip the first character
    } else {
        printf("%s: ", buffer);
    }
    vprintf(format, argptr);

    va_end(argptr);
}

// The function that logs error messages with timestamp
void perror_log(const char *format, ...) {
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
    fprintf(stderr, "%s: ", buffer);
    vfprintf(stderr, format, argptr);

    perror("");

    va_end(argptr);
}

// Initialize the GPIO chip and lines
int initialize_gpio(void) {
    chip = gpiod_chip_open_by_name(CHIP);
    if (!chip) {
        perror_log("Open chip failed\n");
        return 1;
    }

    red_line = gpiod_chip_get_line(chip, LED_R_LINE_NUMBER);
    yellow_line = gpiod_chip_get_line(chip, LED_Y_LINE_NUMBER);
    green_line = gpiod_chip_get_line(chip, LED_G_LINE_NUMBER);
    if (!red_line || !yellow_line || !green_line) {
        perror_log("Get line failed\n");
        gpiod_chip_close(chip);
        return 1;
    }

    gpiod_line_request_output(red_line, "led", 0);
    gpiod_line_request_output(yellow_line, "led", 0);
    gpiod_line_request_output(green_line, "led", 0);

    return 0;
}

// Release the lines and close the GPIO chip
void cleanup_gpio(void) {
    // Turn off all LEDs
    gpiod_line_set_value(red_line, 0); 
    gpiod_line_set_value(yellow_line, 0);
    gpiod_line_set_value(green_line, 0);
    gpiod_line_release(red_line);
    gpiod_line_release(yellow_line);
    gpiod_line_release(green_line);
    gpiod_chip_close(chip);
}

// This function will set the state of an LED
// color: 'R', 'G', or 'Y'
// state: 0 for off, 1 for on
void set_led(char color, int state) {
    struct gpiod_line *line_on, *line_off1, *line_off2;

    switch (color) {
    case 'R':
        line_on = red_line;
        line_off1 = yellow_line;
        line_off2 = green_line;
        break;
    case 'Y':
        line_on = yellow_line;
        line_off1 = red_line;
        line_off2 = green_line;
        break;
    case 'G':
        line_on = green_line;
        line_off1 = red_line;
        line_off2 = yellow_line;
        break;
    default:
        fprintf(stderr, "Invalid color: %c\n", color);
        return;
    }

    gpiod_line_set_value(line_on, state);
    if (state == 1) {
        gpiod_line_set_value(line_off1, 0);
        gpiod_line_set_value(line_off2, 0);
    }
}

typedef struct {
    unsigned char MB;
    unsigned char ME;
    unsigned char CF;
    unsigned char SR;
    unsigned char IL;
    unsigned char TNF;
    unsigned char type_length;
    unsigned int payload_length;
    unsigned char id_length;
    unsigned char* type;
    unsigned char* id;
    unsigned char* payload;
} NdefRecord;

typedef struct {
    unsigned int record_count;
    NdefRecord* records;
} NdefMessage;

volatile sig_atomic_t interrupted = 0;

// This function will be called when SIGINT is sent to the program (Ctrl+C)
void handle_sigint(int sig) {
	interrupted = 1;
	cleanup_gpio();
	exit(0);
}

void sleep_interruptible(int ms) {
    for (int i = 0; i < ms; i++) {
        usleep(1000); // Sleep for 1ms
        if (interrupted) { // Check if a signal has been received
	    break;
        }
    }
}

// Signal handler for SIGUSR1
void handle_sigusr1(int sig) {
    // Set the LED here
    set_led('G', 1);
    sleep_interruptible(500);
}

char* get_machine_id() {
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
/*
void print_hex(const uint8_t *pbtData, const size_t szBytes) {
  for (size_t szPos = 0; szPos < szBytes; szPos++) {
    printf("%02x ", pbtData[szPos]);
  }
  printf("\n");
}
*/

void print_hex(const uint8_t *pbtData, const size_t szBytes) {
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

void send_post_request(char *url, const char *payload) {
    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url);

        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload);

        res = curl_easy_perform(curl);

        if(res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
	}
        curl_easy_cleanup(curl);
    }
}

NdefMessage parse_ndef_message(unsigned char* data, unsigned int length) {
    NdefRecord* records = malloc(length * sizeof(NdefRecord));
    unsigned int record_count = 0;

    unsigned int i = 2;

    // Parse the records
    while (i < length) {
        // Parse the header byte
        unsigned char header = data[i];
        i++;

        // Extract the flags from the header
        unsigned char mb = (header & 0x80) >> 7;
        unsigned char me = (header & 0x40) >> 6;
        unsigned char cf = (header & 0x20) >> 5;
        unsigned char sr = (header & 0x10) >> 4;
        unsigned char il = (header & 0x08) >> 3;
        unsigned char tnf = header & 0x07;

        // Parse the type length
        unsigned char type_length = data[i];
        i++;

        // Parse the payload length
        unsigned int payload_length;
        if (sr) {
            payload_length = data[i];
            i++;
        } else {
            payload_length = (data[i] << 24) | (data[i + 1] << 16) | (data[i + 2] << 8) | data[i + 3];
            i += 4;
        }

        // Parse the ID length
        unsigned char id_length = 0;
        if (il) {
            id_length = data[i];
            i++;
        }

        // Parse the type, ID, and payload
        unsigned char* type = NULL;
        unsigned char* id = NULL;
        unsigned char* payload = NULL;

        if (type_length > 0) {
            type = malloc(type_length);
            memcpy(type, data + i, type_length);
            i += type_length;
        }

        if (id_length > 0) {
            id = malloc(id_length);
            memcpy(id, data + i, id_length);
            i += id_length;
        }

        if (payload_length > 0) {
            payload = malloc(payload_length);
            memcpy(payload, data + i, payload_length);
            i += payload_length;
        }

        // Create a record and add it to the array
        NdefRecord record = {mb, me, cf, sr, il, tnf, type_length, payload_length, id_length, type, id, payload};
        records[record_count++] = record;

        // If this record has the ME flag set, stop parsing
        if (me) {
            break;
        }
    }

    // Create the NdefMessage struct
    NdefMessage message = {record_count, records};

    return message;
}

void free_ndef_message(NdefMessage* message) {
    if (message == NULL) {
        return;
    }

    for (unsigned int i = 0; i < message->record_count; i++) {
        NdefRecord* record = &(message->records[i]);
        free(record->type);
        free(record->id);
        free(record->payload);
    }

    free(message->records);
}

void print_payload_as_ascii(NdefRecord* record) {
    if (record->payload == NULL) {
        print_log("None");
        return;
    }

    if (record->TNF == 1 && record->payload_length >= 3 && record->payload[0] == 0x02) {
        // Text record
        char message[record->payload_length + 20];  // Extra space for the initial text and the null terminator
	sprintf(message, "Text (%d bytes): ", record->payload_length - 3);

	for (unsigned int j = 3; j < record->payload_length; j++) {
	    sprintf(message + strlen(message), "%c", record->payload[j]);
	}

	print_log(message);
    } else if (record->TNF == 1 && record->payload_length >= 1 && record->payload[0] == 0x04) {
        // URI record
	char message[record->payload_length + 20];  // Extra space for the initial text and the null terminator
	sprintf(message, "URI (%d bytes): https://www.", record->payload_length - 3);

	for (unsigned int j = 3; j < record->payload_length; j++) {
	    sprintf(message + strlen(message), "%c", record->payload[j]);
	}

	print_log(message);
    } else {
        // Other types
	char message[record->payload_length + 20];  // Extra space for the initial text and the null terminator
	sprintf(message, "Payload (%d bytes): ", record->payload_length - 3);

	for (unsigned int j = 3; j < record->payload_length; j++) {
	    sprintf(message + strlen(message), "%02c", record->payload[j]);
	}

	print_log(message);
    }
}

void format_payload_as_ascii_without_type(NdefRecord* record, char* payload_ascii) {
    if (record->payload == NULL) {
        strcpy(payload_ascii, "None");
        return;
    }

    if (record->TNF == 1 && record->payload_length >= 3 && record->payload[0] == 0x02) {
        // Text record
        strncpy(payload_ascii, (char*)record->payload + 3, record->payload_length - 3);
    } else if (record->TNF == 1 && record->payload_length >= 1 && record->payload[0] == 0x04) {
        // URI record
        strcpy(payload_ascii, "https://www.");
        strncat(payload_ascii, (char*)record->payload + 1, record->payload_length - 1);
    } else {
        // Other types
        strcpy(payload_ascii, "Unsupported record type");
    }
}

void send_nfc_to_airtable(NdefMessage message, char* uid, int uid_length) {
    // If there are no records, return immediately
    print_log("Sending NFC Message -> Airtable\n");
    if (message.record_count == 0) {
        print_log("No NDEF records to process.\n");
        return;
    }
    // Convert UID to hexadecimal string
    long long int uid_number = 0;
    for (int i = 0; i < uid_length; i++) {
        uid_number = (uid_number << 8) | (unsigned char)uid[i];
    }
    char* uid_hex = malloc(15); // enough space for a 7-byte (14 hex digits) number, plus null terminator
    sprintf(uid_hex, "%014llx", uid_number);
    // Get machine ID
    char* machine_id = get_machine_id();
    if (machine_id == NULL) {
        // handle error
	print_log("Failed Sending: Could not find Machine ID\n");
        return;
    }
    /*
    // Set the TZ environment variable to the desired time zone
    setenv("TZ", "EST", 1);
    tzset();

    // Get the current time and format it as an ISO 8601 string
    time_t rawtime;
    struct tm* timeinfo;
    char timestamp[25]; // enough space for "YYYY-MM-DDTHH:MM:SS.000Z"

    time(&rawtime);
    timeinfo = gmtime(&rawtime); // using UTC time
    strftime(timestamp, 25, "%Y-%m-%dT%H:%M:%S.000Z", timeinfo);
    */
    char url[] = "https://hooks.airtable.com/workflows/v1/genericWebhook/appZUSMwDABUaufib/wflvbbVevox2uQESS/wtrSLYKU4WCoW44kl";
    // Allocate enough space for all payloads combined
    /*
    char* combined_payload = malloc(1024 * message.record_count); // allocate enough space for all payloads combined
    combined_payload[0] = '\0'; // Initialize the combined_payload string to be empty
    //printf("Allocated combined_payload.\n");
    
    for (unsigned int i = 0; i < message.record_count; i++) {
	NdefRecord* record = &(message.records[i]);
        if (record == NULL || record->payload == NULL) {
		return;
	}
        printf("Record %d payload: ", i);
        print_payload_as_ascii(record);
        printf("\n");

        // Convert payload to ASCII
        char* payload_ascii = malloc(record->payload_length + 1);
        format_payload_as_ascii_without_type(record, payload_ascii);
        // Append each payload to the combined_payload string
        strncat(combined_payload, payload_ascii, 1024 * message.record_count); // assume each payload is less than 1024 bytes
        strncat(combined_payload, ",", 1024 * message.record_count); // add a comma between each payload

        free(payload_ascii);
    }
    */
    // Create JSON object
    json_object * jobj = json_object_new_object();
    json_object *jstring = json_object_new_string(uid_hex);
    //json_object *jstring2 = json_object_new_string(combined_payload);
    //json_object *jstring3 = json_object_new_string(timestamp);
    json_object *jstring4 = json_object_new_string(machine_id);
    json_object_object_add(jobj,"Tag ID", jstring);
    //json_object_object_add(jobj,"Payload", jstring2);
    //json_object_object_add(jobj,"Timestamp", jstring3);
    json_object_object_add(jobj,"Machine ID", jstring4);
    const char* json_payload = json_object_to_json_string_ext(jobj, JSON_C_TO_STRING_PRETTY);
    send_post_request(url, json_payload);
    print_log("\nSent POST request.\n");

    // Free allocated memory
    //free(combined_payload);
    free(machine_id);
    json_object_put(jobj); // free json object

}

void send_pipe_to_screen(const char * data) {
    int fd;
    fd = open(fifo_path, O_WRONLY);
    write(fd, data, strlen(data) + 1);
    close(fd);
}

int main(int argc, const char *argv[]) {
  // Register the function to call on SIGINT
  struct sigaction sa;

  sa.sa_handler = handle_sigint;
  sa.sa_flags = 0; // or SA_RESTART;
  sigemptyset(&sa.sa_mask);

  if (sigaction(SIGINT, &sa, NULL) == -1) {
    perror_log("sigaction");
    exit(1);
  }
  // Install the signal handler
  if (signal(SIGUSR1, handle_sigusr1) == SIG_ERR) {
      perror_log("Failed to install signal handler");
      exit(1);
  }
  // Register the function to call on SIGTERM
  // We can use the same struct sa because the settings are the same
  if (sigaction(SIGTERM, &sa, NULL) == -1) {
    perror_log("sigaction");
    exit(1);
  }

  if (initialize_gpio() != 0) {
    return 1;
  }
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
  int num_pages = 32;
  int num_bytes = 4;
  uint8_t data_buffer[num_bytes*num_pages];
  memset(data_buffer, 0, sizeof(data_buffer));
  uint8_t last_uid[10];
  bool same_card = false;
  bool can_read = false;
  while(!interrupted){
	if (nfc_initiator_select_passive_target(pnd, nmMifare, NULL, 0, &nt) > 0) {
		print_log("The following (NFC) ISO14443A tag was found:\n");
		print_log("ATQA (SENS_RES): \n");
		print_hex(nt.nti.nai.abtAtqa, 2);
		print_log("UID (NFCID%c): \n", (nt.nti.nai.abtUid[0] == 0x08 ? '3' : '1'));
		print_hex(nt.nti.nai.abtUid, nt.nti.nai.szUidLen);
		print_log("SAK (SEL_RES): \n");
		print_hex(&nt.nti.nai.btSak, 1);
		if (memcmp(nt.nti.nai.abtUid, last_uid, nt.nti.nai.szUidLen) == 0 && same_card) {
			// The same card is still present, don't read it again
			print_log("Same card found!\n");
			sleep_interruptible(10);
			continue;
		}
		memcpy(last_uid, nt.nti.nai.abtUid, nt.nti.nai.szUidLen);
		same_card = true;
		// Loop to read data from multiple pages
		for (uint8_t page = 4; page <= num_pages; page++) {
			uint8_t cmd[2] = {0x30, page}; // 0x30 is the READ command, then the page number
			size_t cmd_len = sizeof(cmd)/sizeof(uint8_t);
			uint8_t page_buffer[16];
			int res;
			if ((res = nfc_initiator_transceive_bytes(pnd, cmd, cmd_len, page_buffer, sizeof(page_buffer), 0)) < 0) {
				print_log("Error while reading the tag: %s\n", "nfc_initiator_transceive_bytes: RF Transmission Error");
			        can_read = false;
				// Continue to the while loop instead of exiting the program
				set_led('R', 1); // Red LED on
				const char * data_to_send = "read_ultralight.c-program-Failed";
				send_pipe_to_screen(data_to_send);
				sleep_interruptible(50);
				break;
			} else {
				can_read = true;
			}
			// Save the read data in the all_pages buffer
			for (int i = 0; i < num_bytes; i++) {
				data_buffer[i+(page-4)*num_bytes] = page_buffer[i];
			}
		}
		// Print the data from all pages
		char message_buffer[num_pages*num_bytes*3 + 2];  // Each byte becomes two hexadecimal digits and a space, plus one for the newline and one for the null terminator
		for (uint8_t i = 0; i < num_pages*num_bytes; i++) {
		    sprintf(message_buffer + i*3, "%02x ", data_buffer[i]);
		}

		message_buffer[num_pages*num_bytes*3] = '\n';  // Add a newline at the end
		message_buffer[num_pages*num_bytes*3 + 1] = '\0';  // Add a null terminator at the end

		print_log(message_buffer);
		NdefMessage message = parse_ndef_message(data_buffer, sizeof(data_buffer));
		if (can_read) {
			send_nfc_to_airtable(message,(char *) last_uid, nt.nti.nai.szUidLen);
			set_led('G', 1); // Green LED on
			char uid_str[2*nt.nti.nai.szUidLen + 1];
			for (int i = 0; i < nt.nti.nai.szUidLen; i++) {
                            sprintf(uid_str + 2 * i, "%02X", last_uid[i]);
                        }
			char data_to_send_buffer[24 + sizeof(uid_str)];
			strcpy(data_to_send_buffer, "read_ultralight.c-program-");
			strcat(data_to_send_buffer, uid_str);
			send_pipe_to_screen((const char *) data_to_send_buffer);
		}
		free_ndef_message(&message);
		// Wait for 100ms before the next loop iteration
		sleep_interruptible(10); // usleep function takes microseconds, so multiply by 1000
	} else if(same_card) {
		// No card was detected, wait for 500ms
		sleep_interruptible(10);
		// If no card is detected after 500ms, set same_card to false
		if (nfc_initiator_select_passive_target(pnd, nmMifare, NULL, 0, &nt) <= 0) {
			print_log("Tag was released\n");
			same_card = false;
		}
		can_read = false;
	} else {
		sleep_interruptible(10);
		print_log("No tag detected\n");
		can_read = false;
        	set_led('Y', 1); // Yellow LED on
        }
	if (can_read) {
		print_log("Tag read and sent to Airtable\n");
	}
	//clock_gettime(CLOCK_MONOTONIC, &end);
        //double time_spent = (end.tv_sec - start.tv_sec) +
        //                    (end.tv_nsec - start.tv_nsec) / 1e9;
        //print_log("Time spent: %f seconds\n", time_spent);
  }
  nfc_close(pnd);
  nfc_exit(context);
  cleanup_gpio();
  exit(EXIT_SUCCESS);
}
