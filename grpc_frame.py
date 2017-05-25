#!/usr/bin/env python2
from protowire import int2bytes, encode_int_little_endian

def encode_int_big_endian(v, bits):
    return encode_int_little_endian(v, bits)[::-1]

def encode_grpc_frame(msg):
    return '\x00' + encode_int_big_endian(len(msg), 32) + msg

if __name__ == '__main__':
    import sys
    sys.stdout.write(encode_grpc_frame(sys.stdin.read()))
