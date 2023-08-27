#!/bin/sh
cd $HOME/NFC_Tracking
for file in *.c; do
    output="${file%.*}"
    gcc -o "$output" "$file" -l nfc -l curl -l json-c -l gpiod
done
