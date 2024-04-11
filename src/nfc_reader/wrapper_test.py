from ctypes import CDLL, c_char_p

lib = CDLL("./poll.so")

lib.poll.restype = c_char_p

print(lib.poll())

