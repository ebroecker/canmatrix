# -*- coding: utf-8 -*-
# Copyright (c) 2013, Eduard Broecker
# With contributions 2025, Gabriele Omodeo Vanone
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,   PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR  OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import attr
import warnings
import typing
from canmatrix.exceptions import ArbitrationIdOutOfRange, J1939NeedsExtendedIdentifier
@attr.s
class ArbitrationId(object):
    standard_id_mask = ((1 << 11) - 1)
    extended_id_mask = ((1 << 29) - 1)
    compound_extended_mask = (1 << 31)

    id = attr.ib(default=None)
    extended = attr.ib(default=False)  # type: bool

    def __attrs_post_init__(self):
        if self.extended is None:
            # Mimicking old behaviour for now -- remove in the future
            self.extended = True
            warnings.warn(
                "Please set 'extended' attribute as a boolean instead of "
                "None when creating an instance of ArbitrationId class",
                DeprecationWarning
            )
        if self.extended:
            mask = self.extended_id_mask
        else:
            mask = self.standard_id_mask

        if self.id != self.id & mask:
            raise ArbitrationIdOutOfRange('ID out of range')

    @property
    def j1939_pgn(self):
        return self.pgn

    @property
    def pgn(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        # PGN is bits 8-25 of the 29-Bit Extended CAN-ID
        # Made up of PDU-S (8-15), PDU-F (16-23), Data Page (24) & Extended Data Page (25)
        # If PDU-F >= 240 the PDU-S is interpreted as Group Extension
        # If PDU-F < 240 the PDU-S is interpreted as a Destination Address
        _pgn = 0
        if self.j1939_pdu_format == 2:
            _pgn += self.j1939_ps
        _pgn += self.j1939_pf << 8
        _pgn += self.j1939_dp << 16
        _pgn += self.j1939_edp << 17

        return _pgn

    @pgn.setter
    def pgn(self, value):  # type: (int) -> None
        self.extended = True
        _pgn = value & 0x3FFFF
        self.id &= 0xfc0000ff
        self.id |= (_pgn << 8 & 0x3FFFF00)  # default pgn is None -> mypy reports error

    @property
    def j1939_tuple(self):  # type: () -> typing.Tuple[int, int, int]
        """Get tuple (destination, PGN, source)

        :rtype: tuple"""

        return self.j1939_destination, self.pgn, self.j1939_source

    @property
    def j1939_destination(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        if self.j1939_pdu_format == 1:
            destination = self.j1939_ps
        else:
            destination = None
        return destination

    @property
    def j1939_source(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        return self.id & 0xFF

    @j1939_source.setter
    def j1939_source(self, value):  # type: (int) -> None
        self.extended = True
        self.id = (self.id & 0xffffff00) | (value & 0xff)

    @property
    def j1939_ps(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        return (self.id >> 8) & 0xFF

    @property
    def j1939_pf(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        return (self.id >> 16) & 0xFF

    @property
    def j1939_pdu_format(self):
        return 1 if (self.j1939_pf < 240) else 2

    @property
    def j1939_dp(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        return (self.id >> 24) & 0x1

    @property
    def j1939_edp(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        return (self.id >> 25) & 0x1

    @property
    def j1939_priority(self):
        if not self.extended:
            raise J1939NeedsExtendedIdentifier
        return (self.id >> 26) & 0x7

    @j1939_priority.setter
    def j1939_priority(self, value):  # type: (int) -> None
        self.extended = True
        self.id = (self.id & 0x3ffffff) | ((value & 0x7) << 26)

    @property
    def j1939_str(self):  # type: () -> str
        return "DA:0x{da:02X} PGN:0x{pgn:04X} SA:0x{sa:02X}".format(
            da=self.j1939_destination, pgn=self.pgn, sa=self.j1939_source)


    @classmethod
    def from_compound_integer(cls, i):  # type: (typing.Any) -> ArbitrationId
        return cls(
            id=i & cls.extended_id_mask,
            extended=(i & cls.compound_extended_mask) != 0,
        )

    @classmethod
    def from_pgn(cls, pgn):  # type: (int) -> ArbitrationId
        return cls(
            id = (pgn << 8), extended = True
        )

    def to_compound_integer(self):
        if self.extended:
            return self.id | self.compound_extended_mask
        else:
            return self.id

    def __eq__(self, other):
        return (
            self.id == other.id
            and (
                self.extended is None
                or other.extended is None
                or self.extended == other.extended
            )
        )
