# Protowire

Write protobuf messages from the command line:

        ./pw [tag number] [data type] (value) > output.bin
        
where data type is one of protobuf datatypes. If value is not given, it is read from STDIN.

### Examples

To write a protobuf message conforming to, e.g., `message Test1 { int32 a = 1; }` such that `a` has the value 150, write

        ./pw 1 int32 150 > message.bin

Then examine (cf. [official docs](https://developers.google.com/protocol-buffers/docs/encoding#simple)):
        
        $ hd /tmp/msg.bin
        00000000  08 96 01                                          |...|
        00000003

Another example: `message Test2 { string b = 2; }` with `b = "testing"`:

        ./pw 2 string testing

More complex examples can be composed using standard UNIX tools

        ./pw 1 int 150 | ./pw 3 bytes
        
or

        (./pw 1 fixed64 10 && ./pw 2 bool true) | ./pw 4 bytes

### GRPC frames

Wrap into a GRPC frame

        ./pw 1 string "my query" | ./grpc_frame.py wrap > request.bin
        nghttp -H ":method: POST" -H "Content-Type: application/grpc" -H "TE: trailers" \
            --data=request.bin \
            http://localhost:8000/MyGrpcService/MyMethod \
            | ./grpc_frame.py unwrap > /tmp/output.bin

