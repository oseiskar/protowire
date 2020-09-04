from .wire_type import VARINT, FIXED64, LENGTH_DELIM, FIXED32
from .protobuf import get_python_int_struct_fmt
import struct

def read_gen_blocking(f, n):
    left = n
    while left > 0:
        c = f.read(left)
        yield c
        left -= len(c)
        if len(c) == 0:
            raise RuntimeError("unexpected EOF while reading %d bytes" % n)

def read_blocking(f, n):
    return b''.join(read_gen_blocking(f, n))

def read_varint(in_stream):
    value = 0
    bitshift = 0
    while True:
        b = in_stream.read(1)
        if b == b'':
            raise EOFError("EOF while reading varint")
        bits = ord(b)
        value = value | ((bits & 0x7f) << bitshift)
        bitshift += 7
        if (bits & 0x80) == 0:
            return value

def read_protobuf_message(in_stream):
    tag = read_varint(in_stream)
    wire_type = tag & 0x7
    field_number = tag >> 3
    if wire_type == LENGTH_DELIM:
        l = read_varint(in_stream)
        msg = read_blocking(in_stream, l)
    elif wire_type == VARINT:
        msg = read_varint(in_stream)
    elif wire_type == FIXED32:
        msg = read_blocking(in_stream, 4)
    elif wire_type == FIXED64:
        msg = read_blocking(in_stream, 8)
    else:
        raise RuntimeError("unsupported wire type %d" % wire_type)
    return (msg, field_number, wire_type)

def parse_stream(in_stream):
    while True:
        try:
            yield read_protobuf_message(in_stream)
        except EOFError:
            break

def parse_string(msg_string):
    from io import BytesIO
    in_stream = BytesIO(msg_string)
    return list(parse_stream(in_stream))

def decode_zigzag(value):
    v = value // 2
    if value % 2 == 0:
        return v
    return - v - 1

def decode_int_little_endian(value, n_bits, signed=True):
    return struct.unpack(get_python_int_struct_fmt(n_bits, signed), value)[0]

def decode_float(value, bits):
    if bits == 32:
        return struct.unpack('<f', value)[0]
    if bits == 64:
        return struct.unpack('<d', value)[0]
    assert(False)
    return None

DECODERS = {
    "string": lambda v: v.decode('utf-8'),
    "bytes": lambda v: v,
    "float": lambda v: decode_float(v, 32),
    "double": lambda v: decode_float(v, 64),
    "bool": lambda v: { 0: False, 1: True }[v],
    "int": lambda v: v,
    "int32": lambda v: v,
    "int64": lambda v: v,
    "sint32": decode_zigzag,
    "sint64": decode_zigzag,
    "fixed32": lambda v: decode_int_little_endian(v, 32, signed=False),
    "fixed64": lambda v: decode_int_little_endian(v, 64, signed=False),
    "sfixed32": lambda v: decode_int_little_endian(v, 32, signed=True),
    "sfixed64":  lambda v: decode_int_little_endian(v, 64, signed=True)
}

def decode_field(value_bytes, protobuf_type):
    if protobuf_type not in DECODERS:
        raise RuntimeError("invalid type " + protobuf_type)
    return DECODERS[protobuf_type](value_bytes)

# simple stream generator, assumes LENGTH_DELIM wire_tyep, ignores fields
def protobuf_stream_gen(in_stream):
    for entry in parse_stream(in_stream):
        yield entry[0]
