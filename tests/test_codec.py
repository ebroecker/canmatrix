#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `canmatrix` package."""
import os
import unittest
import tempfile

from canmatrix import formats
from canmatrix.canmatrix import Signal, ArbitrationId


class TestCanmatrixCodec(unittest.TestCase):
    """Tests for `canmatrix` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    # def test_bitstruct_format(self):
    #     """"""
    #     s1 = Signal('signal')
    #     self.assertEqual(s1.bitstruct_format(), '<s0')

    #     s2 = Signal('signal', size=8)
    #     self.assertEqual(s2.bitstruct_format(), '<s8')

    #     s3 = Signal('signal', size=8, is_signed=False)
    #     self.assertEqual(s3.bitstruct_format(), '<u8')

    #     s4 = Signal('signal', size=8, is_little_endian=False)
    #     self.assertEqual(s4.bitstruct_format(), '>s8')

    def test_encode_by_signal_raw_value(self):
        test_file = "tests/files/dbc/test.dbc"
        for bus in formats.loadp(test_file).values():
            test_frame1 = ArbitrationId(0x123)
            data = {
                'Signal': 2,
                'someTestSignal': 101,
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))
            assert data_bytes == (0, 0xCA, 0x20, 0, 0, 0, 0, 0)

    def test_encode_by_signal_physical_value(self):
        test_file = "tests/files/dbc/test.dbc"
        for bus in formats.loadp(test_file).values():
            test_frame1 = ArbitrationId(0x123)
            data = {
                'someTestSignal': "101",
                'Signal': u'two'
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))
            assert data_bytes == (0, 0x28, 0x20, 0, 0, 0, 0, 0)

    def test_encode_decode_signal_value(self):
        test_file = "tests/files/dbc/test.dbc"
        for bus in formats.loadp(test_file).values():
            test_frame1 = ArbitrationId(0x123)

            data = {
                'Signal': 2,
                'someTestSignal': 101,
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))
            decoded = bus.decode(test_frame1, data_bytes)

            for k, v in data.items():
                assert decoded[k].raw_value == v

    def test_encode_decode_signal_value_choice_unicode(self):
        test_file = "tests/files/dbc/test.dbc"
        for bus in formats.loadp(test_file).values():
            test_frame1 = ArbitrationId(0x123)

            data = {
                'Signal': u'two'
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))

            decoded = bus.decode(test_frame1, data_bytes)

            for k, v in data.items():
                assert decoded[k].signal.values[decoded[k].raw_value] == v

    def test_encode_decode_signal_value_choice_str(self):
        test_file = "tests/files/dbc/test.dbc"
        for bus in formats.loadp(test_file).values():
            test_frame1 = ArbitrationId(0x123)

            data = {
                'Signal': 'two'
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))

            decoded = bus.decode(test_frame1, data_bytes)

            for k, v in data.items():
                assert decoded[k].signal.values[decoded[k].raw_value] == v

    def test_import_export_additional_frame_info(self):
        test_file = "tests/files/dbc/test.dbc"
        dbs = formats.loadp(test_file)
        tmp_dir = tempfile.mkdtemp()
        # for extension in ['csv', 'json']: # json will not export None type
        for extension in ['csv']:
            out_file_name = tmp_dir + "/output." + extension
            formats.dumpp(dbs, out_file_name, additionalFrameAttributes="UserFrameAttr")
            with open(out_file_name, "r") as file:
                data = file.read()
            self.assertIn("UserFrameAttr", data)


if __name__ == "__main__":
    unittest.main()
