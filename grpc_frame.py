#!/usr/bin/env python2
from protowire import int2bytes, encode_int_little_endian, encode_message

def encode_int_big_endian(v, bits):
    return encode_int_little_endian(v, bits)[::-1]
    
def decode_int_big_endian(bytestr):
    v = 0
    for b in bytestr:
        v = (v << 8) | ord(b)
    return v

def encode_grpc_frame(msg):
    return '\x00' + encode_int_big_endian(len(msg), 32) + msg

def read_gen_blocking(f, n):
    left = n
    while left > 0:
        c = f.read(left)
        yield c
        left -= len(c)
        if len(c) == 0:
            raise RuntimeError("unexpected EOF while reading %d bytes" % n)
        
def read_blocking(f, n):
    return ''.join([c for c in read_gen_blocking(f, n)])

def pipe_blocking(in_stream, out_stream, n):
    for c in read_gen_blocking(f, n):
        out_stream.write(c)
    
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

if __name__ == '__main__':

    import argparse, sys

    parser = argparse.ArgumentParser(description='Wrap / unwrap protobufs to GRPC frames')
    parser.add_argument('command', choices=['wrap', 'unwrap'])
    parser.add_argument('--stream', action='store_true')
    parser.add_argument('--tag', type=int, default=1)
    #parser.add_argument('--wire_type', type=int, default=LENGTH_DELIM)

    args = parser.parse_args()
    
    in_stream = sys.stdin
    out_stream = sys.stdout
    
    if args.command == 'wrap':
        out_stream.write(encode_grpc_frame(in_stream.read()))
    elif args.command == 'unwrap':
        if args.stream:
            while True:
                try:
                    frame = read_grpc_frame(in_stream)
                    out_stream.write(encode_message(args.tag, "bytes", frame))
                except EOFError:
                    break
        else:
            pipe_unwrap_grpc_frame(in_stream, out_stream)

