from .wire_type import VARINT, FIXED64, LENGTH_DELIM, FIXED32
from .protobuf import get_python_int_struct_fmt
import binascii
import struct
from io import BytesIO

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
        raise RuntimeError("unsupported wire type %d with field %d" % (wire_type, field_number))
    return (msg, field_number, wire_type)

def parse_stream(in_stream):
    while True:
        try:
            yield read_protobuf_message(in_stream)
        except EOFError:
            break

def parse_bytes(msg_string):
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
    "hex": lambda v: binascii.hexlify(v).decode('utf-8'),
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
    "sfixed64": lambda v: decode_int_little_endian(v, 64, signed=True)
}

WIRE_TYPES = {
    "string": LENGTH_DELIM,
    "bytes": LENGTH_DELIM,
    "hex": LENGTH_DELIM,
    "float": FIXED32,
    "double": FIXED64,
    "bool": VARINT,
    "int": VARINT,
    "int32": VARINT,
    "int64": VARINT,
    "sint32": VARINT,
    "sint64": VARINT,
    "fixed32": FIXED32,
    "fixed64": FIXED64,
    "sfixed32": FIXED32,
    "sfixed64": FIXED64
}

def decode_field(value_bytes, protobuf_type):
    if protobuf_type not in DECODERS:
        raise RuntimeError("invalid type " + protobuf_type)
    return DECODERS[protobuf_type](value_bytes)

def parse_stream_with_spec(in_stream, spec):
    result = {}
    def decode_msg(msg, field, wire_type, decoder):
        if str(decoder) in DECODERS:
            if WIRE_TYPES[decoder] != wire_type:
                raise RuntimeError("invalid wire type %d for field %s" % (wire_type, field))
            return decode_field(msg, decoder)
        if isinstance(decoder, list):
            # To Do: support packed repeated fields
            return [decode_msg(msg, field, wire_type, decoder[0])]
        if isinstance(decoder, dict):
            return parse_bytes_with_spec(msg, decoder)
        raise RuntimeError("invalid decoder spec " + str(decoder))

    if not isinstance(spec, dict):
        raise RuntimeError("invalid spec (expected dict): " + str(spec))

    for msg, field, wire in parse_stream(in_stream):
        field = str(field)
        if field in spec:
            decoded = decode_msg(msg, field, wire, spec[field])
            if isinstance(decoded, list):
                if field not in result: result[field] = []
                result[field].extend(decoded)
            else:
                result[field] = decoded

    return result

def parse_bytes_with_spec(string, spec):
    if str(spec) in DECODERS:
        return decode_field(string, spec)
    in_stream = BytesIO(string)
    return parse_stream_with_spec(in_stream, spec)

def parse_spec(spec):
    # to allow both { 2: [{ 1:float }] } and { 2: [1:float] }
    if spec[0] == '{':
        return parse_spec(spec[:-1])

    def split_on_closing(s, begin, end):
        # note: no escaping is like "im a { string" is possible here
        count = 0
        for i in range(len(s)):
            if s[i] == begin: count += 1
            elif s[i] == end:
                count -= 1
                if count == 0:
                    return s[1:i], s[i+1:]
        raise RuntimeError("invalid syntax: expected %s before the end of %s" % (end, s))

    if spec in DECODERS: return spec

    tag, _, rest = spec.partition(':')
    tag = str(int(tag))
    result = {}
    if rest[0] == '[':
        sub, rest = split_on_closing(rest, '[', ']')
        result[tag] = [parse_spec(sub)]

    elif rest[0] == '{':
        sub, rest = split_on_closing(rest, '{', '}')
        result[tag] = parse_spec(sub)
    else:
        parts = rest.split(',')
        sub = parts[0]
        if sub not in DECODERS:
            raise RuntimeError('invalid decoder ' + sub)
        result[tag] = sub
        rest = ','.join(parts[1:])
        if len(rest) > 0: rest = ',' + rest
    if len(rest) > 0:
        if rest[0] != ',':
            raise RuntimeError("syntax error: expected ',' to begin %s" % rest)
        rest = rest[1:]

        for field, decoder in parse_spec(rest).items():
            result[field] = decoder

    return result

# simple stream generator, assumes LENGTH_DELIM wire_tyep, ignores fields
def protobuf_stream_gen(in_stream):
    for entry in parse_stream(in_stream):
        yield entry[0]
