from src.utils.nfc_reader_utils import NFCTag
from src.utils.utils import NFCType


def main():

    # Test NFCTag
    nfc_tag = NFCTag(device_id='123456',
                     timestamp=0.0,
                     type=NFCType.EMPLOYEE,
                     data={
                         'unifi_id': 1234,
                         'name': 'John Doe'
                     },
                     tag_id='1234567890')
    print(nfc_tag)
    nfc_dict = dict(nfc_tag)
    print(nfc_dict['data'])

if __name__ == '__main__':
    main()
