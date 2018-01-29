#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `canmatrix` package."""
import collections
import unittest

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

        s2 = Signal('signal', signalSize=8)
        self.assertEqual(s2.bitstruct_format(), '<s8')

        s3 = Signal('signal', signalSize=8, is_signed=False)
        self.assertEqual(s3.bitstruct_format(), '<u8')

        s4 = Signal('signal', signalSize=8, is_little_endian=False)
        self.assertEqual(s4.bitstruct_format(), '>s8')

    def test_encode_signal(self):
        s1 = Signal('signal', signalSize=8)
        self.assertEqual(s1.phys2raw(), 0)
        self.assertEqual(s1.phys2raw(1), 1)
        self.assertEqual(s1.phys2raw(s1.max), 127)
        self.assertEqual(s1.phys2raw(s1.min), -128)

        s2 = Signal('signal', signalSize=10, is_signed=False)
        self.assertEqual(s2.phys2raw(), 0)
        self.assertEqual(s2.phys2raw(10), 10)
        self.assertEqual(s2.phys2raw(s2.max), 1023)
        self.assertEqual(s2.phys2raw(s2.min), 0)

        s3 = Signal('signal', signalSize=8, factor=2)
        self.assertEqual(s3.phys2raw(), 0)
        self.assertEqual(s3.phys2raw(10), 5)
        self.assertEqual(s3.phys2raw(s3.max), 127)
        self.assertEqual(s3.phys2raw(s3.min), -128)

        s4 = Signal('signal', signalSize=8, is_signed=False, factor=5)
        self.assertEqual(s4.phys2raw(), 0)
        self.assertEqual(s4.phys2raw(10), 2)
        self.assertEqual(s4.phys2raw(s4.max), 255)
        self.assertEqual(s4.phys2raw(s4.min), 0)

        s5 = Signal('signal', signalSize=8, offset=2)
        self.assertEqual(s5.phys2raw(), 0)
        self.assertEqual(s5.phys2raw(10), 8)
        self.assertEqual(s5.phys2raw(s5.max), 127)
        self.assertEqual(s5.phys2raw(s5.min), -128)

        s6 = Signal('signal', signalSize=8, is_signed=False, offset=5)
        self.assertEqual(s6.phys2raw(), 0)
        self.assertEqual(s6.phys2raw(10), 5)
        self.assertEqual(s6.phys2raw(s6.max), 255)
        self.assertEqual(s6.phys2raw(s6.min), 0)

        s7 = Signal('signal', signalSize=8)
        s7.addAttribute('GenSigStartValue', '5')
        self.assertEqual(s7.phys2raw(), 5)

        s8 = Signal('signal', signalSize=8, is_signed=False, offset=5)
        s8.addAttribute('GenSigStartValue', '5')
        self.assertEqual(s8.phys2raw(), 5)

        s9 = Signal('signal', signalSize=16, is_signed=False, factor=0.001)
        self.assertEqual(s9.phys2raw(), 0)
        self.assertEqual(s9.phys2raw(s9.max), 65534)
        self.assertEqual(s9.phys2raw(s9.min), 0)
        self.assertEqual(s9.phys2raw(50.123), 50123)

        s10 = Signal('signal', signalSize=8, is_signed=False, factor=0.00005)
        self.assertEqual(s10.phys2raw(), 0)
        self.assertEqual(s10.phys2raw(s10.max), 255)
        self.assertEqual(s10.phys2raw(s10.min), 0)
        self.assertEqual(s10.phys2raw(0.005), 100)
        self.assertEqual(s10.phys2raw(0.003), 60)

        s11 = Signal('signal', signalSize=8)

        with self.assertRaises(ValueError):
            s11.enum2raw('a')

        enumeration = collections.OrderedDict((
            ('a', 0),
            ('b', 1),
            ('c', 2),
        ))
        for name, value in enumeration.items():
            s11.addValues(value=value, valueName=name)

        with self.assertRaises(TypeError):
            s11.enum2raw()

        with self.assertRaises(ValueError):
            s11.enum2raw('')

        with self.assertRaises(ValueError):
            s11.enum2raw(0)

        with self.assertRaises(TypeError):
            s11.raw2enum()

        with self.assertRaises(ValueError):
            s11.raw2enum('')

        with self.assertRaises(ValueError):
            s11.raw2enum(-1)

        for name, value in enumeration.items():
            self.assertEqual(s11.enum2raw(name), value)
            self.assertEqual(s11.raw2enum(value), name)

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

    def test_decode_signal(self):
        s1 = Signal('signal', signalSize=8)
        self.assertEqual(s1.raw2phys(1), 1)
        self.assertEqual(s1.raw2phys(127), s1.max)
        self.assertEqual(s1.raw2phys(-128), s1.min)

        s2 = Signal('signal', signalSize=10, is_signed=False)
        self.assertEqual(s2.raw2phys(10), 10)
        self.assertEqual(s2.raw2phys(s2.max), 1023)
        self.assertEqual(s2.raw2phys(s2.min), 0)

        s3 = Signal('signal', signalSize=8, factor=2)
        self.assertEqual(s3.raw2phys(5), 10)
        self.assertEqual(s3.raw2phys(127), s3.max)
        self.assertEqual(s3.raw2phys(-128), s3.min)

        s4 = Signal('signal', signalSize=8, is_signed=False, factor=5)
        self.assertEqual(s4.raw2phys(2), 10)
        self.assertEqual(s4.raw2phys(255), s4.max)
        self.assertEqual(s4.raw2phys(0), s4.min)

        s5 = Signal('signal', signalSize=8, offset=2)
        self.assertEqual(s5.raw2phys(8), 10)
        self.assertEqual(s5.raw2phys(127), s5.max)
        self.assertEqual(s5.raw2phys(-128), s5.min)

        s6 = Signal('signal', signalSize=8, is_signed=False, offset=5)
        self.assertEqual(s6.raw2phys(5), 10)
        self.assertEqual(s6.raw2phys(255), s6.max)
        self.assertEqual(s6.raw2phys(0), s6.min)

        s7 = Signal('signal', signalSize=16, is_signed=False, factor=0.001)
        self.assertEqual(s7.raw2phys(65535), s7.max)
        self.assertEqual(s7.raw2phys(0), s7.min)
        self.assertEqual(s7.raw2phys(50123), 50.123)

        s8 = Signal('signal', signalSize=8, is_signed=False, factor=0.00005)
        self.assertEqual(s8.raw2phys(255), s8.max)
        self.assertEqual(s8.raw2phys(0), s8.min)
        self.assertEqual(s8.raw2phys(1), 5e-05)
        self.assertEqual(s8.raw2phys(2), 0.0001)
        self.assertAlmostEqual(s8.raw2phys(3), 0.00015)

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

