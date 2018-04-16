Write protobuf messages from the command line::

    pw (field number) [data type] (value) > output.bin

where *data type* is one of the `protobuf datatypes <https://developers.google.com/protocol-buffers/docs/proto3#scalar>`_
(or *int* = *int32* = *int64*). If *value* is not given, it is read from STDIN.
The field number can be omitted and defaults to 1.

This enables creating protobuf messages for GRPC calls or other purposes without a protobuf compiler.
The ``pw`` tool has no library dependencies (plain Python 2) and does not need the ``.proto`` files or any code generated from them.

See the `project Github page <https://github.com/oseiskar/protowire>`_ for full documentation.
