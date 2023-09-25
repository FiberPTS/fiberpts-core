#!/bin/sh

# Navigate to the NFC_Tracking directory in the user's home directory.
cd $HOME/NFC_Tracking

# Loop through all C source files in the current directory.
for file in *.c; do
    # Extract the filename without the .c extension to use as the output binary name.
    output="${file%.*}"

    # Compile the C source file using gcc.
    # Link the compiled code with the following libraries: nfc, curl, json-c, and gpiod.
    gcc -o "$output" "$file" -l nfc -l curl -l json-c -l gpiod
done
