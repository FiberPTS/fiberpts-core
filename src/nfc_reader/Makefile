CC=gcc
CFLAGS=-I/opt/libnfc-1.8.0/include -I/opt/libnfc-1.8.0
LDFLAGS=-lnfc
SRC_DIR=src/nfc_reader
UTILS_DIR=/opt/libnfc-1.8.0/utils
EXEC=nfc_reader

all: $(EXEC)

$(EXEC): $(SRC_DIR)/nfc_reader.c
	$(CC) -o $@ $< $(UTILS_DIR)/nfc-utils.o $(CFLAGS) $(LDFLAGS)

clean:
	rm -f $(EXEC)

.PHONY: all clean
