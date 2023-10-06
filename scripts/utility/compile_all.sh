#!/bin/sh

# Define a function to check if a file includes a certain header or keyword
needs_lib() {
    grep -q "$1" "$2"
}

# Function to compile based on dependencies
compile_with_dependencies() {
    file="$1"
    output="${file%.*}"
    libs=""

    # Check for headers or specific function calls and add associated libraries
    needs_lib "#include <nfc.h>" "$file" && libs="$libs -l nfc"
    needs_lib "#include <curl.h>" "$file" && libs="$libs -l curl"
    needs_lib "#include <json.h>" "$file" && libs="$libs -l json-c"
    needs_lib "#include <gpiod.h>" "$file" && libs="$libs -l gpiod"

    gcc -o "$output" "$file" $libs
}

# Navigate to directories and compile
cd $HOME/FiberPTS/src/iot
for file in *.c; do
    compile_with_dependencies "$file"
done

cd $HOME/FiberPTS/src/iot/utility
for file in *.c; do
    compile_with_dependencies "$file"
done
