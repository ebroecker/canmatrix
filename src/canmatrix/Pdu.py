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

import typing
import attr

from canmatrix.SignalGroup import SignalGroup
from canmatrix.Signal import Signal
from canmatrix.AutosarE2EProperties import AutosarE2EProperties
from canmatrix.AutosarSecOCProperties import AutosarSecOCProperties

@attr.s(eq=False)
class Pdu(object):
    """
    Represents a PDU.

    PDUs are hierarchical groups of signals which are needed to represent Flexray busses
    Whereas a PDU is the same than a frame on CAN bus, at flexray a frame may consist of
    multiple PDUs (a bit like multiple signal layout for multiplexed can frames).
    This class is only used for flexray busses.
    Note: since container-pdus are supported for arxml, this class is also used for arxml (but only
          for sub-pdus of container-pdus).
    """

    name = attr.ib(default="")  # type: str
    size = attr.ib(default=0)  # type: int
    id = attr.ib(default=0)  # type: int
    triggering_name = attr.ib(default="")  # type: str
    pdu_type = attr.ib(default="")  # type: str
    port_type = attr.ib(default="")  # type: str
    signals = attr.ib(factory=list)  # type: typing.MutableSequence[Signal.Signal]
    signalGroups = attr.ib(factory=list)  # type: typing.MutableSequence[SignalGroup.SignalGroup]
    cycle_time = attr.ib(default=0)  # type: int
    secOC_properties = attr.ib(default=None)  # type: Optional[AutosarSecOCProperties.AutosarSecOCProperties]
    # offset is used for arxml, sub-pdu inside a static-container-pdu
    offset_bytes = attr.ib(default=0)  # type: int

    def add_signal(self, signal):
        # type: (Signal) -> Signal
        """
        Add Signal to Pdu.

        :param Signal signal: Signal to be added.
        :return: the signal added.
        """
        self.signals.append(signal)
        return self.signals[len(self.signals) - 1]

    def add_signal_group(self, 
                         Name: str, 
                         Id: int, 
                         signalNames: typing.Sequence[str], 
                         e2e_properties: typing.Optional[AutosarE2EProperties] = None) -> None:
        """Add new SignalGroup to the Frame. Add given signals to the group.

        :param str Name: Group name
        :param int Id: Group id
        :param list of str signalNames: list of Signal names to add. Non existing names are ignored.
        """
        newGroup = SignalGroup(Name, Id, e2e_properties=e2e_properties)
        self.signalGroups.append(newGroup)
        for signal in signalNames:
            signal = signal.strip()
            if signal.__len__() == 0:
                continue
            signalId = self.signal_by_name(signal)
            if signalId is not None:
                newGroup.add_signal(signalId)

    def get_signal_group_for_signal(self, signal_to_find):
        for signal_group in self.signalGroups:
            for signal in signal_group:
                if signal == signal_to_find:
                    return signal_group
        return None

    def signal_by_name(self, name):
        # type: (str) -> typing.Union[Signal, None]
        """
        Get signal by name.

        :param str name: signal name to be found.
        :return: signal with given name or None if not found
        """
        for signal in self.signals:
            if signal.name == name:
                return signal
        return None
