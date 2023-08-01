#include <stdio.h>
#include <stdlib.h>

int main() {
    system("sh pull.sh");
    system("sh compile_all.sh");
    system("sh update_permissions.sh");
    return 0;
}