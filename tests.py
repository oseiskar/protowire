# -*- coding: utf-8 -*-

import unittest

from protowire import *
from grpc_frame import *

class TestProtoWire(unittest.TestCase):

    def test_encode_varint(self):
        self.assertEquals(encode_varint(8), '\x08')
        self.assertEquals(encode_varint(150), '\x96\x01')
        
    def test_encode_message_varints(self):
        self.assertEquals(encode_message(1, "int32", 0), '')
        self.assertEquals(encode_message(1, "int64", 0), '')
        self.assertEquals(encode_message(1, "int32", '0'), '')
        self.assertEquals(encode_message(1, "int64", '0'), '')
        self.assertEquals(encode_message(2, "int32", 0), '')
        self.assertEquals(encode_message(3, "int64", 0), '')
        self.assertEquals(encode_message(1, "sint32", 0), '')
        self.assertEquals(encode_message(1, "sint64", 0), '')
        self.assertEquals(encode_message(1, "int32", 150), '\x08\x96\x01')
        self.assertEquals(encode_message(3, "int64", 100), '\x18\x64')
        self.assertEquals(encode_message(4, "sint32", -100), '\x20\xC7\x01')
        self.assertEquals(encode_message(4, "sint64", -100), '\x20\xC7\x01')
        self.assertEquals(encode_message(2, "int32", -1), '\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01')
        self.assertEquals(encode_message(2, "int64", -1), '\x10\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01')
    
    def test_encode_message_floats(self):
        self.assertEquals(encode_message(1, "float", 0.0), '')
        self.assertEquals(encode_message(2, "double", 0.0), '')
        self.assertEquals(encode_message(10, "float", 3.141592), '\x55\xd8\x0f\x49\x40')
        self.assertEquals(encode_message(11, "double", 3.141592), '\x59\x7a\x00\x8b\xfc\xfa\x21\x09\x40')
        self.assertEquals(encode_message(10, "float", float('inf')), '\x55\x00\x00\x80\x7f')
        self.assertEquals(encode_message(10, "float", float('nan')), '\x55\x00\x00\xc0\x7f')
        self.assertEquals(encode_message(11, "double", '-inf'), '\x59\x00\x00\x00\x00\x00\x00\xf0\xff')
        
    def test_repeated_packed(self):
        self.assertEquals(encode_message(14, "int32", []), '')
        self.assertEquals(encode_message(13, "fixed64", []), '')
        self.assertEquals(encode_message(14, "int32", [1,2,3]), '\x72\x03\x01\x02\x03')
        self.assertEquals(encode_message(13, "fixed64", [1,2]),
            '\x6a\x10\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00')
        self.assertEquals(encode_message(13, "fixed64", [0,0]),
            '\x6a\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertEquals(encode_message(14, "int32", [0]), '\x72\x01\x00')
        self.assertEquals(encode_message(14, "int32", [0, 0]), '\x72\x02\x00\x00')
        self.assertEquals(encode_message(14, "bool", ["false", "true"]), '\x72\x02\x00\x01')
        
    def test_encode_message_bool(self):
        self.assertEquals(encode_message(12, "bool", "true"), '\x60\x01')
        self.assertEquals(encode_message(12, "bool", "True"), '\x60\x01')
        self.assertEquals(encode_message(12, "bool", "TRUE"), '\x60\x01')
        self.assertEquals(encode_message(12, "bool", "false"), '')
        self.assertEquals(encode_message(12, "bool", "False"), '')
        self.assertEquals(encode_message(12, "bool", "FALSE"), '')
        
    def test_encode_message_fixed(self):
        self.assertEquals(encode_message(6, "fixed32", 0), '')
        self.assertEquals(encode_message(7, "fixed64", 0), '')
        self.assertEquals(encode_message(8, "sfixed32", 0), '')
        self.assertEquals(encode_message(9, "sfixed64", 0), '')
        self.assertEquals(encode_message(6, "fixed32", 345045678), '\x35\xAE\xFA\x90\x14')
        self.assertEquals(encode_message(7, "fixed64", 345045678), '\x39\xAE\xFA\x90\x14\x00\x00\x00\x00')
        self.assertEquals(encode_message(8, "sfixed32", -100), '\x45\x9C\xFF\xFF\xFF')
        self.assertEquals(encode_message(9, "sfixed64", -100), '\x49\x9C\xFF\xFF\xFF\xFF\xFF\xFF\xFF')
        
    def test_encode_message_strings(self):
        self.assertEquals(encode_message(1, "string", ""), '')
        self.assertEquals(encode_message(1, "bytes", ""), '')
        self.assertEquals(encode_message(1, "string", "hello!"), '\x0A\x06hello!')
        self.assertEquals(encode_message(1, "bytes", "hello!"), '\x0A\x06hello!')
        self.assertEquals(encode_message(1, "string", u"hello!"), '\x0A\x06hello!')
        self.assertEquals(encode_message(1, "bytes", u"hello!"), '\x0A\x06hello!')
        self.assertEquals(encode_message(1, "string", u"öäå☺"), '\x0a\x09\xc3\xb6\xc3\xa4\xc3\xa5\xe2\x98\xba')
        self.assertEquals(encode_message(1, "bytes", '\xc3\xb6\xc3\xa4\xc3\xa5\xe2\x98\xba'),
            '\x0a\x09\xc3\xb6\xc3\xa4\xc3\xa5\xe2\x98\xba')
            
    def test_big_endian(self):
        self.assertEquals(decode_int_big_endian('\xde\xad\xbe\xef'), 0xdeadbeef)
        self.assertEquals(encode_uint32_big_endian(0xdeadbeef), '\xde\xad\xbe\xef'), 

    def test_encode_grpc_frame(self):
        self.assertEquals(encode_grpc_frame('\xde\xad\xbe\xef'), '\x00\x00\x00\x00\x04\xde\xad\xbe\xef')
        
    def test_bash(self):
    
        import subprocess
        
        def checkBash(cmd, expected):
            actual = subprocess.check_output(["bash", "-c", cmd])
            self.assertEquals(actual, expected)
        
        checkBash(
            """((./pw string hello | ./pw bytes) && (./pw 2 int 3 5 | ./pw bytes)) |
            ./grpc_frame.py wrap --stream |
            ./grpc_frame.py unwrap --stream | 
            ./grpc_frame.py wrap |
            ./grpc_frame.py unwrap""",
            '\x0a\x07\x0a\x05\x68\x65\x6c\x6c\x6f\x0a\x04\x12\x02\x03\x05')
            
        checkBash(
            """((./pw 3 bool true | ./pw bytes) && (./pw 2 int 3 5 | ./pw bytes)) |
            ./grpc_frame.py wrap --stream""",
            '\x00\x00\x00\x00\x02\x18\x01\x00\x00\x00\x00\x04\x12\x02\x03\x05')
            
        checkBash("./pw int 0", '')
        checkBash("./pw string ''", '')
        checkBash("./pw 2 int 0", '')
            

if __name__ == '__main__':
    unittest.main()

