# -*- coding: utf-8 -*-

import unittest

import protowire.wire_type
from protowire.proto_decoding import parse_string, decode_field, decode_zigzag
from protowire.protobuf import encode_message, encode_varint, encode_zigzag
from protowire.grpc_frame import encode_grpc_frame, \
    encode_uint32_big_endian, decode_int_big_endian

class TestUnits(unittest.TestCase):

    def test_encode_varint(self):
        self.assertEqual(encode_varint(8), b'\x08')
        self.assertEqual(encode_varint(150), b'\x96\x01')

    def test_encode_message_varints(self):
        self.assertEqual(encode_message(1, "int32", 0), b'')
        self.assertEqual(encode_message(1, "int64", 0), b'')
        self.assertEqual(encode_message(1, "int32", '0'), b'')
        self.assertEqual(encode_message(1, "int64", '0'), b'')
        self.assertEqual(encode_message(2, "int32", 0), b'')
        self.assertEqual(encode_message(3, "int64", 0), b'')
        self.assertEqual(encode_message(1, "sint32", 0), b'')
        self.assertEqual(encode_message(1, "sint64", 0), b'')
        self.assertEqual(encode_message(1, "int32", 150), b'\x08\x96\x01')
        self.assertEqual(encode_message(3, "int64", 100), b'\x18\x64')
        self.assertEqual(encode_message(4, "sint32", -100), b'\x20\xC7\x01')
        self.assertEqual(encode_message(4, "sint64", -100), b'\x20\xC7\x01')
        self.assertEqual(encode_message(2, "int32", -1), b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01')
        self.assertEqual(encode_message(2, "int64", -1), b'\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01')

    def test_encode_message_floats(self):
        self.assertEqual(encode_message(1, "float", 0.0), b'')
        self.assertEqual(encode_message(2, "double", 0.0), b'')
        self.assertEqual(encode_message(10, "float", 3.141592), b'\x55\xd8\x0f\x49\x40')
        self.assertEqual(encode_message(11, "double", 3.141592), b'\x59\x7a\x00\x8b\xfc\xfa\x21\x09\x40')
        self.assertEqual(encode_message(10, "float", float('inf')), b'\x55\x00\x00\x80\x7f')
        self.assertEqual(encode_message(10, "float", float('nan')), b'\x55\x00\x00\xc0\x7f')
        self.assertEqual(encode_message(11, "double", '-inf'), b'\x59\x00\x00\x00\x00\x00\x00\xf0\xff')

    def test_repeated_packed(self):
        self.assertEqual(encode_message(14, "int32", []), b'')
        self.assertEqual(encode_message(13, "fixed64", []), b'')
        self.assertEqual(encode_message(14, "int32", [1,2,3]), b'\x72\x03\x01\x02\x03')
        self.assertEqual(encode_message(13, "fixed64", [1,2]),
            b'\x6a\x10\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00')
        self.assertEqual(encode_message(13, "fixed64", [0,0]),
            b'\x6a\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertEqual(encode_message(14, "int32", [0]), b'\x72\x01\x00')
        self.assertEqual(encode_message(14, "int32", [0, 0]), b'\x72\x02\x00\x00')
        self.assertEqual(encode_message(14, "bool", ["false", "true"]), b'\x72\x02\x00\x01')

    def test_encode_message_bool(self):
        self.assertEqual(encode_message(12, "bool", "true"), b'\x60\x01')
        self.assertEqual(encode_message(12, "bool", "True"), b'\x60\x01')
        self.assertEqual(encode_message(12, "bool", "TRUE"), b'\x60\x01')
        self.assertEqual(encode_message(12, "bool", "false"), b'')
        self.assertEqual(encode_message(12, "bool", "False"), b'')
        self.assertEqual(encode_message(12, "bool", "FALSE"), b'')

    def test_encode_message_fixed(self):
        self.assertEqual(encode_message(6, "fixed32", 0), b'')
        self.assertEqual(encode_message(7, "fixed64", 0), b'')
        self.assertEqual(encode_message(8, "sfixed32", 0), b'')
        self.assertEqual(encode_message(9, "sfixed64", 0), b'')
        self.assertEqual(encode_message(6, "fixed32", 345045678), b'\x35\xAE\xFA\x90\x14')
        self.assertEqual(encode_message(7, "fixed64", 345045678), b'\x39\xAE\xFA\x90\x14\x00\x00\x00\x00')
        self.assertEqual(encode_message(8, "sfixed32", -100), b'\x45\x9C\xFF\xFF\xFF')
        self.assertEqual(encode_message(9, "sfixed64", -100), b'\x49\x9C\xFF\xFF\xFF\xFF\xFF\xFF\xFF')

    def test_encode_message_strings(self):
        self.assertEqual(encode_message(1, "string", ""), b'')
        self.assertEqual(encode_message(1, "bytes", ""), b'')
        self.assertEqual(encode_message(1, "string", "hello!"), b'\x0A\x06hello!')
        self.assertEqual(encode_message(1, "bytes", "hello!"), b'\x0A\x06hello!')
        self.assertEqual(encode_message(1, "string", u"hello!"), b'\x0A\x06hello!')
        self.assertEqual(encode_message(1, "bytes", u"hello!"), b'\x0A\x06hello!')
        self.assertEqual(encode_message(1, "string", u"öäå☺"), b'\x0a\x09\xc3\xb6\xc3\xa4\xc3\xa5\xe2\x98\xba')
        self.assertEqual(encode_message(1, "bytes", b'\xc3\xb6\xc3\xa4\xc3\xa5\xe2\x98\xba'),
            b'\x0a\x09\xc3\xb6\xc3\xa4\xc3\xa5\xe2\x98\xba')

    def test_big_endian(self):
        self.assertEqual(decode_int_big_endian(b'\xde\xad\xbe\xef'), 0xdeadbeef)
        self.assertEqual(encode_uint32_big_endian(0xdeadbeef), b'\xde\xad\xbe\xef')

    def test_encode_grpc_frame(self):
        self.assertEqual(encode_grpc_frame(b'\xde\xad\xbe\xef'), b'\x00\x00\x00\x00\x04\xde\xad\xbe\xef')

    def test_parse_strings(self):
        messages = parse_string(b'\x0A\x06hello!\x39\xAE\xFA\x90\x14\x00\x00\x00\x00\x18\x64\x45\x9C\xFF\xFF\xFF\x55\xd8\x0f\x49\x40')
        self.assertEquals(len(messages), 5)

        msg, field, wire = messages[0]
        self.assertEquals(field, 1)
        self.assertEquals(msg, b'hello!')
        self.assertEquals(wire, protowire.wire_type.LENGTH_DELIM)
        self.assertEquals(decode_field(msg, 'string'), u'hello!')
        self.assertEquals(decode_field(msg, 'bytes'), b'hello!')

        msg, field, wire = messages[1]
        self.assertEquals(field, 7)
        self.assertEquals(msg, b'\xAE\xFA\x90\x14\x00\x00\x00\x00')
        self.assertEquals(wire, protowire.wire_type.FIXED64)
        self.assertEquals(decode_field(msg, 'fixed64'), 345045678)

        msg, field, wire = messages[2]
        self.assertEquals(field, 3)
        self.assertEquals(msg, 100)
        self.assertEquals(wire, protowire.wire_type.VARINT)

        msg, field, wire = messages[3]
        self.assertEquals(field, 8)
        self.assertEquals(msg, b'\x9C\xFF\xFF\xFF')
        self.assertEquals(wire, protowire.wire_type.FIXED32)
        self.assertEquals(decode_field(msg, 'sfixed32'), -100)

        msg, field, wire = messages[4]
        self.assertEquals(field, 10)
        self.assertEquals(msg, b'\xd8\x0f\x49\x40')
        self.assertEquals(wire, protowire.wire_type.FIXED32)
        self.assertLess(abs(decode_field(msg, 'float') - 3.141592), 1e-7)

    def test_zigzag(self):
        self.assertEqual(encode_zigzag(2147483647, 32), 4294967294)
        self.assertEqual(decode_zigzag(4294967294), 2147483647)
        self.assertEqual(encode_zigzag(-1, 64), 1)
        self.assertEqual(encode_zigzag(2, 32), 4)
        self.assertEqual(decode_zigzag(1), -1)
        self.assertEqual(decode_zigzag(4), 2)
        self.assertEqual(decode_zigzag(3), -2)

    def test_signed(self):
        self.assertEqual(decode_field(b'\xFF\xFF\xFF\xFF', 'sfixed32'), -1)
        self.assertEqual(decode_field(b'\xFF\xFF\xFF\xFF', 'fixed32'), 0xffffffff)
        self.assertEqual(decode_field(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF', 'sfixed64'), -1)
        self.assertEqual(decode_field(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF', 'fixed64'), 0xffffffffffffffff)



class TestCommandLine(unittest.TestCase):
    def test_bash(self):
        import subprocess

        def getOutputBash(cmd):
            return subprocess.check_output(["bash", "-c", cmd])

        self.assertEqual(getOutputBash(
            """((pw string hello | pw bytes) && (pw 2 int 3 5 | pw bytes)) |
            pw-grpc-frame wrap --stream |
            pw-grpc-frame unwrap --stream |
            pw-grpc-frame wrap |
            pw-grpc-frame unwrap"""),
            b'\x0a\x07\x0a\x05\x68\x65\x6c\x6c\x6f\x0a\x04\x12\x02\x03\x05')

        self.assertEqual(getOutputBash(
            """((pw 3 bool true | pw bytes) && (pw 2 int 3 5 | pw bytes)) |
            pw-grpc-frame wrap --stream"""),
            b'\x00\x00\x00\x00\x02\x18\x01\x00\x00\x00\x00\x04\x12\x02\x03\x05')

        longMsg = "a"*200
        longMsgOut = getOutputBash(
            """pw string %s |
            pw-grpc-frame wrap --stream |
            pw-grpc-frame unwrap --stream""" % longMsg)

        self.assertEqual(len(longMsgOut), 203)

        self.assertEqual(getOutputBash("pw int 0"), b'')
        self.assertEqual(getOutputBash("pw string ''"), b'')
        self.assertEqual(getOutputBash("pw 2 int 0"), b'')

if __name__ == '__main__':
    unittest.main()
