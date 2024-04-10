import nfc

def main():
    clf = nfc.ContactlessFrontend('tty:AML6:pn532')
    if clf:
        print("Device is connected")
        clf.close()
    else:
        print("Failed to connect to the device")

if __name__ == "__main__":
    main()
