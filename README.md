

# Protowire [![Build Status](https://travis-ci.org/oseiskar/protowire.svg?branch=master)](https://travis-ci.org/oseiskar/protowire)

Write protobuf messages from the command line:

    ./pw (field number) [data type] (value) > output.bin
        
where `data type` is one of the [protobuf datatypes](https://developers.google.com/protocol-buffers/docs/proto3#scalar) (or `int` = `int32` = `int64`). If `value` is not given, it is read from STDIN.
The field number can be left out and defaults to 1.

This enables creating protobuf messages for GRPC calls or other purposes without a protobuf compiler. The `pw` tool has no library dependencies (plain Python 2) and does not need the `.proto` files or any code generated from them.

### Examples

To write a protobuf message conforming to, e.g., `message Test1 { int32 a = 1; }` such that `a` has the value 150, write

    ./pw 1 int32 150 > message.bin

Then examine (cf. [official docs](https://developers.google.com/protocol-buffers/docs/encoding#simple)):
        
    $ hd /tmp/msg.bin
    00000000  08 96 01                                          |...|
    00000003

Another example: `message Test2 { string b = 2; }` with `b = "testing"`:

    ./pw 2 string testing

More complex examples (also from [here](https://developers.google.com/protocol-buffers/docs/encoding#embedded)) can be composed using standard UNIX tools

    ./pw int 150 | ./pw 3 bytes
        
and

    (./pw fixed64 10 && ./pw 2 bool true) | ./pw 4 bytes

## GRPC client

This tool requires the `grpcio` Python package.

    ./grpc_client.py (-is) (-os) (--tag 1) host:port/path

Consider the following example:

```protobuf
syntax = "proto3";

message RequestThing {
    string query = 1;
}

message ResponseItem {
    int32 foo = 1;
    // ...
}

service MyService {
    rpc UnaryMethod(RequestThing) returns (ResponseItem) {}
    rpc ServerStream(RequestThing) returns (stream ResponseItem) {}
    rpc ClientStream(stream RequestThing) returns (ResponseItem) {}
    rpc BidirectionalStream(stream RequestThing) returns (stream ResponseItem) {}
}

// helper collections
message RequestCollection {
    repeated RequestThing things = 1;
}

message ResponseCollection {
    repeated ResponseItem items = 1;
}
```

An **`UnaryMethod`** call using a `RequestThing` with `query = "hello"` can be sent to a server running at `localhost:8000` as follows:

    ./pw string "hello" | \
        ./grpc_client.py localhost:8000/MyService/UnaryMethod \
        > response_item.bin
            
which saves the obtained `ResponseItem` protobuf the file `response_item.bin`.

It is also possible to convert **`ServerStream`** responses to protobuf `ResponseCollection`s using the `-os`/`--stream_response` flag:

    ./pw string "hello" | \
        ./grpc_client.py localhost:8000/MyService/ServerStream -os \
        > response_collection.bin

Similarly, **`ClientStream`** can be constructed from `RequestCollection`s with `-is`/`--stream_request`:

    ./pw string "singleton item" | ./pw 1 bytes | \
        ./grpc_client.py localhost:8000/MyService/ClientStream -is \
        > response_item.bin

The flags `-is` and `-os` can be used simultaneously for **`BidirectionalStream`**

    ((./pw string "first" | ./pw bytes) && (./pw string "second" | ./pw bytes)) | \
        ./grpc_client.py localhost:8000/MyService/BidirectionalStream -is -os \
        > response_collection.bin

In all `-os`-cases, there is also a `--tag` flag that can be used to change the field number in the response protobuf collection. For example `message ResponseCollection { repeated ResponseItem items = 2; }` would require:

    ./pw string "hello" | \
        ./grpc_client.py localhost:8000/MyService/ServerStream -os --tag 2 \
        > response_collection.bin

## GRPC frames for low-level communication

This tool does not need any GRPC or protbuf packages, but can be combined with a HTTP/2 client like `nghttp` to make GRPC calls.
Usage:

    ./grpc_frame.py [wrap|unwrap] (--stream) (--tag 1)

Wrap into a GRPC frame and unwrap the response to normal protobuf:

    ./pw 1 string "my query" | ./grpc_frame.py wrap > request.bin
    nghttp -H ":method: POST" -H "Content-Type: application/grpc" -H "TE: trailers" \
        --data=request.bin \
        http://localhost:8000/MyService/UnaryMethod \
        | ./grpc_frame.py unwrap > /tmp/output.bin

The option `--stream` can be used with both wrap and unwrap to convert protobuf collections to GRPC streams like in the other GRPC client example. The `--tag` option can be used to change the field number in the "unwrapped" protobuf collection.

Notice that older versions of `nghttp` (like 0.6.4 in Debian Jessie) [cannot read STDIN](https://github.com/nghttp2/nghttp2/issues/133) with `-d -`.

