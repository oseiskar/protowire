
def ensure_binary(stream):
    try:
        return stream.buffer # Python 3
    except AttributeError:
        return stream # Python 2

def pw():
    from .protobuf import ENCODERS, encode_message
    import argparse, sys

    # hack parameters to allow defaulting first argument to 1
    field_number_present = True
    field_number = 1
    try:
        len(sys.argv) < 2 or sys.argv[1][0] == '-' or int(sys.argv[1])
    except ValueError:
        field_number_present = False

    parser = argparse.ArgumentParser(description='Write protobuf messages from low-level input')
    if field_number_present:
        parser.add_argument('field_number', type=int, default=field_number)
    parser.add_argument('data_type', choices=ENCODERS.keys(), default='bytes')
    parser.add_argument('values', nargs='*')

    args = parser.parse_args()

    if len(args.values) == 0:
        value = ensure_binary(sys.stdin).read()
    elif len(args.values) == 1:
        value = args.values[0]
    else:
        value = args.values

    if field_number_present:
        field_number = args.field_number

    msg = encode_message(field_number, args.data_type, value)
    ensure_binary(sys.stdout).write(msg)


def grpc_frame():
    from .grpc_frame import wrap_grpc_stream, encode_grpc_frame, \
        unwrap_grpc_stream, pipe_unwrap_grpc_frame

    import argparse, sys

    parser = argparse.ArgumentParser(description='Wrap / unwrap protobufs to GRPC frames')
    parser.add_argument('command', choices=['wrap', 'unwrap'])
    parser.add_argument('--stream', action='store_true')
    parser.add_argument('--tag', type=int, default=1)
    #parser.add_argument('--wire_type', type=int, default=LENGTH_DELIM)

    args = parser.parse_args()

    in_stream = ensure_binary(sys.stdin)
    out_stream = ensure_binary(sys.stdout)

    if args.command == 'wrap':
        if args.stream:
            wrap_grpc_stream(in_stream, out_stream)
        else:
            out_stream.write(encode_grpc_frame(in_stream.read()))
    elif args.command == 'unwrap':
        if args.stream:
            unwrap_grpc_stream(in_stream, out_stream, args.tag)
        else:
            pipe_unwrap_grpc_frame(in_stream, out_stream)


def grpc_client():
    from .grpc_frame import encode_message, protobuf_stream_gen
    # pylint: disable=E0401
    import grpc

    def parse_args():
        import argparse

        parser = argparse.ArgumentParser(description='Simple binary GRPC client')
        parser.add_argument('-is', '--stream_request', action='store_true')
        parser.add_argument('-os', '--stream_response', action='store_true')
        parser.add_argument('--tag', type=int, default=1)
        parser.add_argument('url')

        return parser.parse_args()

    def mode_name(is_stream):
        if is_stream:
            return 'stream'
        return 'unary'

    def client(in_stream, out_stream, args):
        host, _, path = args.url.partition('/')

        channel = grpc.insecure_channel(host)

        # e.g. unary_stream
        mode = mode_name(args.stream_request) + '_' + mode_name(args.stream_response)

        passthrough = lambda x: x

        service = getattr(channel, mode)('/' + path,
            request_serializer=passthrough,
            response_deserializer=passthrough)

        if args.stream_request:
            req = protobuf_stream_gen(in_stream)
        else:
            req = in_stream.read()

        if args.stream_response:
            for item in service(req):
                out_stream.write(encode_message(args.tag, "bytes", item))
        else:
            out_stream.write(service(req))

    import sys
    args = parse_args()
    in_stream = ensure_binary(sys.stdin)
    out_stream = ensure_binary(sys.stdout)
    client(in_stream, out_stream, args)

def pw_decode():
    import json, sys
    from .proto_decoding import parse_stream_with_spec, parse_spec

    def parse_args():
        import argparse
        parser = argparse.ArgumentParser(description='Parse protobuf messages with minimal spec')
        parser.add_argument('spec', help="For example: 2:string,3:{2:float,4:[1:sfixed32]}")
        parser.add_argument('--pretty', action='store_true')
        return parser.parse_args()

    args = parse_args()
    parsed = parse_stream_with_spec(ensure_binary(sys.stdin), parse_spec(args.spec))
    opts = { 'sort_keys': True }
    if args.pretty: opts['indent'] = 2
    print(json.dumps(parsed, **opts))
