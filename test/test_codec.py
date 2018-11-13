#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `canmatrix` package."""
import unittest
import tempfile
import os

from canmatrix import formats
from canmatrix.canmatrix import Signal


class TestCanmatrixCodec(unittest.TestCase):
    """Tests for `canmatrix` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_bitstruct_format(self):
        """"""
        s1 = Signal('signal')
        self.assertEqual(s1.bitstruct_format(), '<s0')

        s2 = Signal('signal', size=8)
        self.assertEqual(s2.bitstruct_format(), '<s8')

        s3 = Signal('signal', size=8, is_signed=False)
        self.assertEqual(s3.bitstruct_format(), '<u8')

        s4 = Signal('signal', size=8, is_little_endian=False)
        self.assertEqual(s4.bitstruct_format(), '>s8')

    def test_encode_canmatrix(self):
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "test", "test.dbc")
        for bus in formats.loadp(db_path).values():
            test_frame1 = 0x123
            data = {
                'Signal': 2,
                'someTestSignal': 101,
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))
            assert data_bytes == (0, 0x28, 0x04, 0, 0, 0, 0, 0)

    def test_encode_decode_signal_value(self):
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "test", "test.dbc")
        for bus in formats.loadp(db_path).values():
            test_frame1 = 0x123

            data = {
                'Signal': 2,
                'someTestSignal': 101,
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))
            decoded = bus.decode(test_frame1, data_bytes, False)

            for k, v in data.items():
                assert decoded[k] == v

    def test_encode_decode_signal_value_choice_unicode(self):
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "test", "test.dbc")
        for bus in formats.loadp(db_path).values():
            test_frame1 = 0x123

            data = {
                'Signal': u'two'
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))

            decoded = bus.decode(test_frame1, data_bytes, True)

            for k, v in data.items():
                assert str(decoded[k]) == v

    def test_encode_decode_signal_value_choice_str(self):
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "test", "test.dbc")
        for bus in formats.loadp(db_path).values():
            test_frame1 = 0x123

            data = {
                'Signal': 'two'
            }
            data_bytes = tuple(bytearray(bus.encode(test_frame1, data)))

            decoded = bus.decode(test_frame1, data_bytes, True)

            for k, v in data.items():
                assert str(decoded[k]) == v

    def test_import_export_additional_frame_info(self):
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "test", "test.dbc")
        dbs = formats.loadp(db_path)
        tmp_dir = tempfile.mkdtemp()
        for extension in ['csv', 'json']:
            out_file_name = tmp_dir + "/output." + extension
            formats.dumpp(dbs, out_file_name, additionalFrameAttributes="UserFrameAttr")
            with open(out_file_name, "r") as file:
                data = file.read()
            self.assertIn("UserFrameAttr", data)


if __name__ == "__main__":
    unittest.main()
