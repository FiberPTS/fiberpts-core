#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include <json-c/json.h>

#define MAX_COMMAND 50
#define MAX_IP_LENGTH 16

char* get_machine_id() {
    FILE* file = fopen("/etc/machine-id", "r");
    if (file == NULL) {
        perror("Unable to open /etc/machine-id");
        return NULL;
    }

    char* machine_id = malloc(33); // the machine ID is a 32-character string, plus '\0' at the end
    if (fgets(machine_id, 33, file) == NULL) {
        perror("Unable to read /etc/machine-id");
        fclose(file);
        return NULL;
    }

    fclose(file);

    return machine_id;
}

void send_post_request(char *url, const char *payload) {
    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;

    curl = curl_easy_init();
    if (curl) {
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload);

        res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        }

        curl_easy_cleanup(curl);
    }
}

int main() {
    return 0;
    char command[MAX_COMMAND];
    char ip_address[MAX_IP_LENGTH];
    char url[] = "https://hooks.airtable.com/workflows/v1/genericWebhook/appZUSMwDABUaufib/wfllY6VRTf8uXLhkW/wtrKdDfdnzPVIufVU";

    FILE *fp = popen("hostname -I", "r");
    if (fp == NULL) {
        perror("Failed to execute command");
        return 1;
    }

    if (fgets(ip_address, sizeof(ip_address), fp) == NULL) {
        perror("Failed to read output");
        return 1;
    }

    pclose(fp);

    // Remove trailing newline from IP address
    size_t len = strlen(ip_address);
    if (len > 0 && ip_address[len - 1] == '\n') {
        ip_address[len - 1] = '\0';
    }

    char* machine_id = get_machine_id();
    if (machine_id == NULL) {
        perror("Failed to get machine ID");
        return 1;
    }

    json_object *jobj = json_object_new_object();
    json_object_object_add(jobj, "IP Address", json_object_new_string(ip_address));
    json_object_object_add(jobj, "Machine ID", json_object_new_string(machine_id));
    const char *json_payload = json_object_to_json_string_ext(jobj, JSON_C_TO_STRING_PLAIN);

    send_post_request(url, json_payload);

    free(machine_id);
    json_object_put(jobj);

    return 0;
}