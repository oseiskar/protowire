#!/usr/bin/env python2
from .protobuf import encode_message
from .proto_decoding import read_blocking, read_gen_blocking, protobuf_stream_gen
import struct

def encode_uint32_big_endian(v):
    return struct.pack('>I', v)

def decode_int_big_endian(bytestr):
    try:
        int_array = [ord(b) for b in bytestr] # Python 2
    except TypeError:
        int_array = bytestr # Python 3
    v = 0
    for b in int_array:
        v = (v << 8) | b
    return v

def encode_grpc_frame(msg):
    return b'\x00' + encode_uint32_big_endian(len(msg)) + msg

def unwrap_grpc_frame(in_stream):
    compressed_flag = in_stream.read(1)
    if compressed_flag == b'':
        raise EOFError('EOF')

    assert(compressed_flag == b'\x00')
    size = decode_int_big_endian(read_blocking(in_stream, 4))
    return read_gen_blocking(in_stream, size)

def pipe_unwrap_grpc_frame(in_stream, out_stream):
    for c in unwrap_grpc_frame(in_stream):
        out_stream.write(c)

def read_grpc_frame(in_stream):
    return b''.join(unwrap_grpc_frame(in_stream))

def wrap_grpc_stream(in_stream, out_stream):
    for msg in protobuf_stream_gen(in_stream):
        out_stream.write(encode_grpc_frame(msg))

def unwrap_grpc_stream(in_stream, out_stream, tag=1):
    while True:
        try:
            frame = read_grpc_frame(in_stream)
            out_stream.write(encode_message(tag, "bytes", frame))
        except EOFError:
            break
