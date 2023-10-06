# Define the compiler
CC = gcc

# Define compile-time flags
CFLAGS = -Wall

# Base directory
BASEDIR = /home/potato/FiberPTS/src/iot

# Include directories
INCLUDES = -I$(BASEDIR)/utility

# Source files
SOURCES = $(BASEDIR)/utility/log_utils.c \
          $(BASEDIR)/utility/signal_utils.c \
          $(BASEDIR)/utility/utils.c \
          $(BASEDIR)/nfc_tap_listener.c \
          $(BASEDIR)/operation_tap_listener.c

# Libraries
LIBS = -lnfc -lgpiod

# Build each .c file to a respective .o object file
OBJECTS = $(SOURCES:.c=.o)

# Build all targets
all: nfc_tap_listener operation_tap_listener

# Linking rule for nfc_tap_listener
nfc_tap_listener: $(OBJECTS)
	$(CC) $(CFLAGS) $(INCLUDES) -o nfc_tap_listener $(BASEDIR)/nfc_tap_listener.o $(BASEDIR)/utility/log_utils.o $(BASEDIR)/utility/signal_utils.o $(BASEDIR)/utility/utils.o $(LIBS)

# Linking rule for operation_tap_listener
operation_tap_listener: $(OBJECTS)
	$(CC) $(CFLAGS) $(INCLUDES) -o operation_tap_listener $(BASEDIR)/operation_tap_listener.o $(BASEDIR)/utility/log_utils.o $(BASEDIR)/utility/signal_utils.o $(BASEDIR)/utility/utils.o $(LIBS)

# Compilation rule to build .o from .c
%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Clean up the build
clean:
	rm -f $(BASEDIR)/*.o $(BASEDIR)/utility/*.o nfc_tap_listener operation_tap_listener