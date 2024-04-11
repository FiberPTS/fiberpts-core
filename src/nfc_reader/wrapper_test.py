from ctypes import CDLL, c_uint8

lib = CDLL("./poll.so")

lib.poll.restype = c_uint8

print(lib.poll())

