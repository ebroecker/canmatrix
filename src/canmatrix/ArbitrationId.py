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


def _check_range(name, value, mask):  # type: (str, int, int) -> None
    if value != value & mask:
        raise ValueError(
            "{name} {value} out of range (0-{maximum})".format(
                name=name, value=value, maximum=mask)
        )


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

    @classmethod
    def from_j1939_fields(cls, pdu_format, pdu_specific, priority=0, edp=0, dp=0,
                          source_address=0):
        # type: (int, int, int, int, int, int) -> ArbitrationId
        """Build an extended ArbitrationId from the individual J1939 bit fields.

        :param pdu_format: PDU Format (PF), 8 bits (0-255)
        :param pdu_specific: PDU Specific (PS), 8 bits (0-255) -- destination
            address (PF < 240) or group extension (PF >= 240)
        :param priority: message priority, 3 bits (0-7)
        :param edp: Extended Data Page, 1 bit (0-1)
        :param dp: Data Page, 1 bit (0-1)
        :param source_address: source address (SA), 8 bits (0-255)
        :rtype: ArbitrationId
        """
        _check_range("priority", priority, 0x7)
        _check_range("edp", edp, 0x1)
        _check_range("dp", dp, 0x1)
        _check_range("pdu_format", pdu_format, 0xFF)
        _check_range("pdu_specific", pdu_specific, 0xFF)
        _check_range("source_address", source_address, 0xFF)
        _id = (
            (priority << 26)
            | (edp << 25)
            | (dp << 24)
            | (pdu_format << 16)
            | (pdu_specific << 8)
            | source_address
        )
        return cls(id=_id, extended=True)

    @classmethod
    def from_pgn_fields(cls, pgn, priority=0, source_address=0, destination=None):
        # type: (int, int, int, typing.Optional[int]) -> ArbitrationId
        """Build an extended ArbitrationId from a PGN plus its surrounding fields.

        :param pgn: Parameter Group Number, 18 bits (0-0x3FFFF)
        :param priority: message priority, 3 bits (0-7)
        :param source_address: source address (SA), 8 bits (0-255)
        :param destination: destination address, 8 bits (0-255). Only valid for
            PDU1 messages (PDU format < 240); raises ValueError otherwise.
        :rtype: ArbitrationId
        """
        _check_range("pgn", pgn, 0x3FFFF)
        _check_range("priority", priority, 0x7)
        _check_range("source_address", source_address, 0xFF)
        _id = (pgn << 8) | (priority << 26) | source_address
        if destination is not None:
            _check_range("destination", destination, 0xFF)
            pdu_format = (_id >> 16) & 0xFF
            if pdu_format >= 240:
                raise ValueError(
                    "destination is only valid for PDU1 messages "
                    "(PDU format < 240)"
                )
            _id |= destination << 8
        return cls(id=_id, extended=True)

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
