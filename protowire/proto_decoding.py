from .protobuf import LENGTH_DELIM

def read_gen_blocking(f, n):
    left = n
    while left > 0:
        c = f.read(left)
        yield c
        left -= len(c)
        if len(c) == 0:
            raise RuntimeError("unexpected EOF while reading %d bytes" % n)

def read_blocking(f, n):
    return b''.join([c for c in read_gen_blocking(f, n)])

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
    if wire_type != LENGTH_DELIM:
        raise RuntimeError("unsupported wire type %d" % wire_type)

    l = read_varint(in_stream)
    msg = read_blocking(in_stream, l)
    return (msg, field_number)

def protobuf_stream_gen(in_stream):
    while True:
        try:
            msg, _ = read_protobuf_message(in_stream)
            yield msg
        except EOFError:
            break
