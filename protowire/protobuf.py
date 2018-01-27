#!/usr/bin/env python2
import struct

# to disalbe incorrect inconsistent-return-statements in encode_float
# pylint: disable=R

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

def encode_int_little_endian(value, n_bits):
    if n_bits == 32:
        return struct.pack('<i', value)
    return struct.pack('<q', value)

def encode_string(s):
    if isinstance(s, unicode):
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

VARINT, FIXED64, LENGTH_DELIM, START_GROUP, END_GROUP, FIXED32 = range(6)

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
        "fixed32": Encoder(FIXED32, lambda v: encode_int_little_endian(v, 32)),
        "fixed64": Encoder(FIXED64, lambda v: encode_int_little_endian(v, 64)),
        "sfixed32": Encoder(FIXED32, lambda v: encode_int_little_endian(v, 32)),
        "sfixed64": Encoder(FIXED64, lambda v: encode_int_little_endian(v, 64)),
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
            return ''

        wire_type = LENGTH_DELIM
        payload = []
        for v in value:
            payload.append(encoder.encode(v))
        payload = "".join(payload)
        payload = encode_varint(len(payload)) + payload
    else:
        if encoder.default_value(value):
            return ''
        wire_type = encoder.wire_type
        payload = encoder.encode(value)

    return encode_key(field_number, wire_type) + payload
