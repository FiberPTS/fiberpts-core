# Compiler and linker configurations
CC := gcc
CFLAGS := -I/opt/libnfc-1.8.0/include -I/opt/libnfc-1.8.0 -fPIC
LDFLAGS := -L/opt/libnfc-1.8.0/lib -lnfc -shared
SRC_DIR := /opt/FiberPTS/src/nfc_reader
UTILS_DIR := /opt/libnfc-1.8.0/utils
LIB_NAME := poll.so

# Define the source file and the utility object file
SRC := $(SRC_DIR)/poll.c
UTILS_OBJ := $(UTILS_DIR)/nfc-utils.o

# Default target
all: $(LIB_NAME)

# Link the program into a shared library
$(LIB_NAME): $(SRC) $(UTILS_OBJ)
	$(CC) -o $@ $(SRC) $(UTILS_OBJ) $(CFLAGS) $(LDFLAGS)

# Clean the build
clean:
	rm -f $(LIB_NAME)

.PHONY: all clean
