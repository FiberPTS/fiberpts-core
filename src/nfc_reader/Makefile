CC := gcc
CFLAGS := -I/opt/libnfc-1.8.0/include -I/opt/libnfc-1.8.0 -fPIC
LDFLAGS := -L/opt/libnfc-1.8.0/utils -lnfc
TARGET := /opt/FiberPTS/src/nfc_reader/nfc_lib.so
SOURCE := /opt/FiberPTS/src/nfc_reader/nfc_lib.c

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -shared -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
