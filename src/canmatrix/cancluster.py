# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import typing
from builtins import *

import canmatrix


class CanCluster(dict):

    def __init__(self, *arg, **kw):
        super(CanCluster, self).__init__(*arg, **kw)
        self._frames = []  # type: typing.List[canmatrix.Frame]
        self._signals = []  # type: typing.List[canmatrix.Signal]
        self._ecus = []  # type: typing.List[canmatrix.Ecu]
        self._pdu_gateway_list = []
        self.update()

    def update_frames(self):  # type: () -> typing.MutableSequence[canmatrix.Frame]
        frames = []  # type: typing.List[canmatrix.Frame]
        frame_names = []  # type: typing.List[str]
        for matrixName in self:
            for frame in self[matrixName].frames:  # type: canmatrix.Frame
                if frame.name not in frame_names:
                    frame_names.append(frame.name)
                    frames.append(frame)
                else:
                    index = frame_names.index(frame.name)
                    for transmitter in frame.transmitters:
                        frames[index].add_transmitter(transmitter)
                    for receiver in frame.receivers:
                        frames[index].add_receiver(receiver)
        self._frames = frames
        return frames

    def update_signals(self):  # type: () -> typing.MutableSequence[canmatrix.Signal]
        signals = []  # type: typing.List[canmatrix.Signal]
        signal_names = []  # type: typing.List[str]
        for matrixName in self:
            for frame in self[matrixName].frames:  # type: canmatrix.Frame
                for signal in frame.signals:
                    if signal.name not in signal_names:
                        signal_names.append(signal.name)
                        signals.append(signal)
                    else:
                        index = signal_names.index(signal.name)
                        for receiver in signal.receivers:
                            signals[index].add_receiver(receiver)
        self._signals = signals
        return signals

    def update_ecus(self):  # type: () -> typing.MutableSequence[canmatrix.Ecu]
        ecus = []  # type: typing.List[canmatrix.Ecu]
        ecu_names = []  # type: typing.List[str]
        for matrixName in self:
            for ecu in self[matrixName].ecus:  # type: canmatrix.Ecu
                if ecu.name not in ecu_names:
                    ecu_names.append(ecu.name)
                    ecus.append(ecu)
        self._ecus = ecus
        return ecus

    def update(self):
        self.update_frames()
        self.update_signals()
        self.update_ecus()

    @property
    def ecus(self):  # type: () -> typing.MutableSequence[canmatrix.Ecu]
        if not self._ecus:
            self.update_ecus()
        return self._ecus

    @property
    def frames(self):  # type: () -> typing.MutableSequence[canmatrix.Frame]
        if not self._frames:
            self.update_frames()
        return self._frames

    @property
    def signals(self):  # type: () -> typing.MutableSequence[canmatrix.Signal]
        if not self._signals:
            self.update_signals()
        return self._signals

    def pdu_gateway(self, pdu_gateway_list=[]):
        self._pdu_gateway_list += pdu_gateway_list
        return self._pdu_gateway_list

    def get_routing_info(self, pdu_name, strict_search=False):
        routing_source = []
        routing_target = []
        if strict_search:
            for pdu in self._pdu_gateway_list:
                if pdu_name == pdu["source"]:
                    routing_source.append(pdu["target"])
                if pdu_name == pdu["target"]:
                    routing_target.append(pdu["source"])
        else:
            for pdu in self._pdu_gateway_list:
                if pdu_name in pdu["source"]:
                    routing_source.append(pdu["target"])
                if pdu_name in pdu["target"]:
                    routing_target.append(pdu["source"])
        return {"source": routing_source, "target": routing_target}
