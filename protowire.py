#!/usr/bin/env python2

def int2bytes(u):
    if not isinstance(u, list):
        u = [u]
    return bytes(bytearray(u))

def encode_varint(value):
    bits = value & 0x7f
    value >>= 7
    bytes = []
    while value:
        bytes.append(0x80|bits)
        bits = value & 0x7f
        value >>= 7
    bytes.append(bits)
    return int2bytes(bytes)

def encode_zigzag(value, bits):
    return (value << 1) ^ (value >> (bits-1))
    
def encode_int_little_endian(value, n_bits):
    a = []
    for b in range(n_bits/8):
        a.append(value & 0xff)
        value = value >> 8
    return int2bytes(a)

def encode_string(s):
    if isinstance(s, unicode):
        b = s.encode('utf-8')
    else:
        b = s
    return encode_varint(len(b)) + b

VARINT, FIXED64, LENGTH_DELIM, START_GROUP, END_GROUP, FIXED32 = range(6)

encode_zigzag_varint = lambda v: encode_varint(encode_zigzag(v))

def define_encoders():
    class Encoder:
        def __init__(self, wire_type, encoder_func, default_value=lambda x: x==0):
            self.wire_type = wire_type
            self.encode = encoder_func
            self.default_value = default_value
            
    bool_string_to_int = lambda s: int(s.lower() == 'true')
    empty_string = lambda s: len(s) == 0
            
    encoders = {
        "string": Encoder(LENGTH_DELIM, encode_string, empty_string),
        "bytes": Encoder(LENGTH_DELIM, encode_string, empty_string),
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
    
    # TODO: floats

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
            
if __name__ == '__main__':
    import argparse, sys
    
    # hack parameters to allow defaulting first argument to 1
    field_number_present = True
    field_number = 1
    try:
        len(sys.argv) < 2 or sys.argv[1][0] == '-' or int(sys.argv[1])
    except:
        field_number_present = False

    parser = argparse.ArgumentParser(description='Write protobuf messages from low-level input')
    if field_number_present:
        parser.add_argument('field_number', type=int, default=field_number)
    parser.add_argument('data_type', choices=ENCODERS.keys(), default='bytes')
    parser.add_argument('values', nargs='*')

    args = parser.parse_args()
    
    if len(args.values) == 0:
        value = sys.stdin.read()
    elif len(args.values) == 1:
        value = args.values[0]
    else:
        value = args.values
        
    if field_number_present:
        field_number = args.field_number

    msg = encode_message(field_number, args.data_type, value)
    sys.stdout.write(msg)

