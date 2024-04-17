CC := gcc
CFLAGS := -I/opt/libnfc/include -I/opt/libnfc -fPIC
LDFLAGS := -L/opt/libnfc/utils -lnfc
TARGET := /opt/FiberPTS/src/nfc_reader/nfc_lib.so
SOURCE := /opt/FiberPTS/src/nfc_reader/nfc_lib.c

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -shared -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
