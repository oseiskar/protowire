#!/usr/bin/env python2
import struct

from .wire_type import VARINT, FIXED64, LENGTH_DELIM, FIXED32

# to disalbe incorrect inconsistent-return-statements in encode_float
# pylint: disable=R

def is_string_like(s):
    try:
        return isinstance(s, unicode) # Python 2
    except NameError:
        return isinstance(s, str) # Python 3

def int2bytes(u):
    if not isinstance(u, list):
        u = [u]
    return bytes(bytearray(u))

def encode_varint(value):
    if value < 0:
        value += (1 << 64)
    bits = value & 0x7f
    value >>= 7
    bytearr = []
    while value:
        bytearr.append(0x80|bits)
        bits = value & 0x7f
        value >>= 7
    bytearr.append(bits)
    return int2bytes(bytearr)

def encode_zigzag(value, bits):
    return (value << 1) ^ (value >> (bits-1))

def get_python_int_struct_fmt(n_bits, signed):
    if n_bits == 32:
        if signed:
            return '<i'
        return '<I'
    else:
        if signed:
            return '<q'
        return '<Q'

def encode_int_little_endian(value, n_bits, signed=True):
    return struct.pack(get_python_int_struct_fmt(n_bits, signed), value)

def encode_string(s):
    if is_string_like(s):
        b = s.encode('utf-8')
    else:
        b = s
    return encode_varint(len(b)) + b

def encode_float(f, bits):
    if bits == 32:
        return struct.pack('<f', f)
    elif bits == 64:
        return struct.pack('<d', f)
    else:
        assert(False)

def define_encoders():
    class Encoder:
        def __init__(self, wire_type, encoder_func, default_value=lambda x: int(x)==0):
            self.wire_type = wire_type
            self.encode = encoder_func
            self.default_value = default_value

    bool_string_to_int = lambda s: int(s.lower() == 'true')
    empty_string = lambda s: len(s) == 0
    zero_float = lambda f: float(f) == 0.0

    encoders = {
        "string": Encoder(LENGTH_DELIM, encode_string, empty_string),
        "bytes": Encoder(LENGTH_DELIM, encode_string, empty_string),
        "float": Encoder(FIXED32, lambda v: encode_float(float(v), 32), zero_float),
        "double": Encoder(FIXED64, lambda v: encode_float(float(v), 64), zero_float),
        "bool": Encoder(VARINT, lambda s: encode_varint(bool_string_to_int(s)), \
            default_value=lambda s: bool_string_to_int(s)==0)
    }

    int_encoders = {
        "int": Encoder(VARINT, encode_varint),
        "int32": Encoder(VARINT, encode_varint),
        "int64": Encoder(VARINT, encode_varint),
        "sint32": Encoder(VARINT, lambda v: encode_varint(encode_zigzag(v, 32))),
        "sint64": Encoder(VARINT, lambda v: encode_varint(encode_zigzag(v, 64))),
        "fixed32": Encoder(FIXED32, lambda v: encode_int_little_endian(v, 32, signed=False)),
        "fixed64": Encoder(FIXED64, lambda v: encode_int_little_endian(v, 64, signed=False)),
        "sfixed32": Encoder(FIXED32, lambda v: encode_int_little_endian(v, 32, signed=True)),
        "sfixed64": Encoder(FIXED64, lambda v: encode_int_little_endian(v, 64, signed=True)),
    }

    for t, e in int_encoders.items():
        encoders[t] = Encoder(e.wire_type, lambda v, e=e: e.encode(int(v)))

    return encoders

ENCODERS = define_encoders()

def encode_key(field_number, wire_type):
    return encode_varint((field_number << 3) | wire_type)

def encode_message(field_number, proto_type, value):

    encoder = ENCODERS[proto_type]

    if isinstance(value, list):
        if len(value) == 0:
            return b''

        wire_type = LENGTH_DELIM
        payload = []
        for v in value:
            payload.append(encoder.encode(v))
        payload = b''.join(payload)
        payload = encode_varint(len(payload)) + payload
    else:
        if encoder.default_value(value):
            return b''
        wire_type = encoder.wire_type
        payload = encoder.encode(value)

    return encode_key(field_number, wire_type) + payload
