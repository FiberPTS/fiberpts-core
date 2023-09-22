#include <stdio.h>
#include <stdlib.h>

int main() {
    system("sh /home/potato/NFC_Tracking/pull.sh");
    system("sh /home/potato/NFC_Tracking/compile_all.sh");
    system("sh /home/potato/NFC_Tracking/update_permissions.sh");
    return 0;
}