#!/bin/sh
cd /home/potato/NFC_Tracking
for file in *.c; do
    output="${file%.*}"
    gcc -o "$output" "$file" -l nfc -l curl -l json-c -lgpiod
done
