from ctypes import CDLL, c_bool, c_char_p, c_size_t, create_string_buffer


def init_poll():
    """
    Initializes and returns a CDLL object for interacting with the 'libpoll.so' shared library.

    Sets the argument types and return type for the 'poll' function within the shared library.
    
    Returns:
        CDLL: Configured library object ready to use for calling the 'poll' function.
    """
    lib = CDLL("./libpoll.so")
    lib.poll.argtypes = [c_char_p, c_size_t]
    lib.poll.restype = None
    lib.is_tag_present.argtypes = None
    lib.is_tag_present.restype = c_bool
    return lib


def main():
    """
    Continuously polls for NFC tags and prints their UID strings decoded from hexadecimal.
    Initializes the NFC polling library and enters a loop to poll for the first tag.
    """
    lib = init_poll()
    uid_len = 64  # Define the buffer size for the UID string

    while True:
        print('Tag detected: ', lib.is_tag_present())
        uid_str = create_string_buffer(uid_len)  # Create a buffer for the UID
        lib.poll(uid_str, uid_len)  # Call the C function to fill the buffer with the UID string
        print("UID String:", uid_str.value.decode('utf-8'))  # Decode and display the UID string
        print('Tag detected: ', lib.is_tag_present())

if __name__ == "__main__":
    main()
