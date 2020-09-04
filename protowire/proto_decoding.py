from .wire_type import VARINT, FIXED64, LENGTH_DELIM, FIXED32

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

def decode_stream(in_stream):
    while True:
        try:
            yield read_protobuf_message(in_stream)
        except EOFError:
            break

def decode_string(msg_string):
    from io import BytesIO
    in_stream = BytesIO(msg_string)
    return list(decode_stream(in_stream))

# simple stream generator, assumes LENGTH_DELIM wire_tyep, ignores fields
def protobuf_stream_gen(in_stream):
    for entry in decode_stream(in_stream):
        yield entry[0]
