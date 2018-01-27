#!/usr/bin/env python
from grpc_frame import encode_message, protobuf_stream_gen

def mode_name(is_stream):
    if is_stream:
        return 'stream'
    return 'unary'

if __name__ == '__main__':

    # pylint: disable=E0401
    import argparse, sys, grpc

    parser = argparse.ArgumentParser(description='Simple binary GRPC client')
    parser.add_argument('-is', '--stream_request', action='store_true')
    parser.add_argument('-os', '--stream_response', action='store_true')
    parser.add_argument('--tag', type=int, default=1)
    parser.add_argument('url')

    args = parser.parse_args()

    host, _, path = args.url.partition('/')

    in_stream = sys.stdin
    out_stream = sys.stdout

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
