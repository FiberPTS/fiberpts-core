#include <stdio.h>
#include <stdlib.h>

int main() {
    // Execute the pull.sh script located in the NFC_Tracking directory.
    // This script pulls the latest changes from the remote repository.
    system("sh /home/potato/NFC_Tracking/pull.sh");

    // Execute the compile_all.sh script located in the NFC_Tracking directory.
    // This script is responsible for compiling all c code files.
    system("sh /home/potato/NFC_Tracking/compile_all.sh");

    // Execute the update_permissions.sh script located in the NFC_Tracking directory.
    // This script is responsible for updating script and program file permissions.
    system("sh /home/potato/NFC_Tracking/update_permissions.sh");

    return 0;
}
