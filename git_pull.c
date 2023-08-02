#include <stdio.h>
#include <stdlib.h>

int main() {
    system("sh ~/NFC_Tracking/pull.sh");
    system("sh ~/NFC_Tracking/compile_all.sh");
    system("sh ~/NFC_Tracking/update_permissions.sh");
    return 0;
}