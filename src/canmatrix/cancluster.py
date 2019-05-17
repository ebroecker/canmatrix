# -*- coding: utf-8 -*-
from __future__ import absolute_import
import typing

import canmatrix.canmatrix as cm


class CanCluster(dict):

    def __init__(self, *arg, **kw):
        super(CanCluster, self).__init__(*arg, **kw)
        self._frames = []  # type: typing.List[cm.Frame]
        self._signals = []  # type: typing.List[cm.Signal]
        self._ecus = []  # type: typing.List[cm.Ecu]
        self.update()

    def update_frames(self):  # type: () -> typing.MutableSequence[cm.Frame]
        frames = []  # type: typing.List[cm.Frame]
        frame_names = []  # type: typing.List[str]
        for matrixName in self:
            for frame in self[matrixName].frames:  # type: cm.Frame
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

    def update_signals(self):  # type: () -> typing.MutableSequence[cm.Signal]
        signals = []  # type: typing.List[cm.Signal]
        signal_names = []  # type: typing.List[str]
        for matrixName in self:
            for frame in self[matrixName].frames:
                for signal in frame.signals:  # type: cm.Signal
                    if signal.name not in signal_names:
                        signal_names.append(signal.name)
                        signals.append(signal)
                    else:
                        index = signal_names.index(signal.name)
                        for receiver in signal.receivers:
                            signals[index].add_receiver(receiver)
        self._signals = signals
        return signals

    def update_ecus(self):  # type: () -> typing.MutableSequence[cm.Ecu]
        ecus = []  # type: typing.List[cm.Ecu]
        ecu_names = []  # type: typing.List[str]
        for matrixName in self:
            for ecu in self[matrixName].ecus:  # type: cm.Ecu
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
    def ecus(self):  # type: () -> typing.MutableSequence[cm.Ecu]
        if not self._ecus:
            self.update_ecus()
        return self._ecus

    @property
    def frames(self):  # type: () -> typing.MutableSequence[cm.Frame]
        if not self._frames:
            self.update_frames()
        return self._frames

    @property
    def signals(self):  # type: () -> typing.MutableSequence[cm.Signal]
        if not self._signals:
            self.update_signals()
        return self._signals
