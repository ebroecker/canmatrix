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

@attr.s(eq=False)
class SignalGroup(object):
    """
    Represents signal-group, containing multiple Signals.
    """
    name = attr.ib()  # type: str
    id = attr.ib()  # type: int
    signals = attr.ib(factory=list, repr=False)  # type: typing.MutableSequence[Signal]
    e2e_properties = attr.ib(default=None)  # type: Optional[AutosarE2EProperties]
    secOC_properties= attr.ib(default=None)  # type: Optional[AutosarSecOCProperties]

    def add_signal(self, signal):  # type: (Signal) -> None
        """Add a Signal to SignalGroup.

        :param Signal signal: signal to add
        """
        if signal not in self.signals:
            self.signals.append(signal)

    def del_signal(self, signal):  # type: (Signal) -> None
        """Remove Signal from SignalGroup.

        :param Signal signal: signal to remove
        """
        if signal in self.signals:
            self.signals.remove(signal)

    def by_name(self, name):  # type: (str) -> typing.Union[Signal, None]
        """
        Find a Signal in the group by Signal name.

        :param str name: Signal name to find
        :return: signal contained in the group identified by name
        :rtype: Signal
        """
        for test in self.signals:
            if test.name == name:
                return test
        return None

    def __iter__(self):  # type: () -> typing.Iterable[Signal]
        """Iterate over all contained signals."""
        return iter(self.signals)

    def __getitem__(self, name):  # type: (str) -> Signal
        signal = self.by_name(name)
        if signal:
            return signal
        raise KeyError("Signal '{}' doesn't exist".format(name))
