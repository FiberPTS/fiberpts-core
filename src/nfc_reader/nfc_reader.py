import nfc

if __name__ == '__main__':
    clf = nfc.ContactlessFrontend()
    print(clf.open('tty:AML6'))