#!/usr/bin/env python2
from .protobuf import encode_message
from .proto_decoding import read_blocking, read_gen_blocking, protobuf_stream_gen
import struct

def encode_uint32_big_endian(v):
    return struct.pack('>I', v)

def decode_int_big_endian(bytestr):
    v = 0
    for b in bytestr:
        v = (v << 8) | ord(b)
    return v

def encode_grpc_frame(msg):
    return '\x00' + encode_uint32_big_endian(len(msg)) + msg

def unwrap_grpc_frame(in_stream):
    compressed_flag = in_stream.read(1)
    if compressed_flag == '':
        raise EOFError('EOF')

    assert(compressed_flag == '\x00')
    size = decode_int_big_endian(read_blocking(in_stream, 4))
    return read_gen_blocking(in_stream, size)

def pipe_unwrap_grpc_frame(in_stream, out_stream):
    for c in unwrap_grpc_frame(in_stream):
        out_stream.write(c)

def read_grpc_frame(in_stream):
    return ''.join([c for c in unwrap_grpc_frame(in_stream)])

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
