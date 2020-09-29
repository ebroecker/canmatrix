# -*- coding: utf-8 -*-
# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

from __future__ import absolute_import, division, print_function

import copy
import logging
import typing
from builtins import *

import canmatrix

logger = logging.getLogger(__name__)

def copy_ecu(ecu_or_glob, source_db, target_db):
    # type: (typing.Union[canmatrix.Ecu, str], canmatrix.CanMatrix, canmatrix.CanMatrix) -> None
    """
    Copy ECU(s) identified by Name or as Object from source CAN matrix to target CAN matrix.
    This function additionally copy all relevant Defines.

    :param ecu_or_glob: Ecu instance or glob pattern for Ecu name
    :param source_db: Source CAN matrix
    :param target_db: Destination CAN matrix
    """
    # check whether ecu_or_glob is object or symbolic name
    if isinstance(ecu_or_glob, canmatrix.Ecu):
        ecu_list = [ecu_or_glob]
    else:
        ecu_list = source_db.glob_ecus(ecu_or_glob)

    for ecu in ecu_list:
        target_db.add_ecu(copy.deepcopy(ecu))
        # copy all ecu-defines
        for attribute in source_db.ecu_defines:
            if ecu.attribute(attribute, source_db) is None:
                continue
            if attribute not in target_db.ecu_defines:
                target_db.add_ecu_defines(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.ecu_defines[attribute].definition))
                target_db.add_define_default(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.ecu_defines[attribute].defaultValue))
            # only default value exists in source but is different to default value in target
            if attribute not in ecu.attributes and ecu.attribute(attribute, source_db) is not None and \
                    ecu.attribute(attribute, source_db) != ecu.attribute(attribute, target_db):
                target_db.ecu_by_name(ecu.name).add_attribute(attribute, ecu.attribute(attribute, source_db))
            # update enum data types if needed:
            if source_db.ecu_defines[attribute].type == 'ENUM':
                temp_attr = ecu.attribute(attribute, db=source_db)
                if temp_attr not in target_db.ecu_defines[attribute].values:
                    target_db.ecu_defines[attribute].values.append(copy.deepcopy(temp_attr))
                    target_db.ecu_defines[attribute].update()


def copy_ecu_with_frames(ecu_or_glob, source_db, target_db, rx=True, tx=True, direct_ecu_only=True):
    # type: (typing.Union[canmatrix.Ecu, str], canmatrix.CanMatrix, canmatrix.CanMatrix) -> None
    """
    Copy ECU(s) identified by Name or as Object from source CAN matrix to target CAN matrix.
    This function additionally copy all relevant Frames and Defines.

    :param ecu_or_glob: Ecu instance or glob pattern for Ecu name
    :param source_db: Source CAN matrix
    :param target_db: Destination CAN matrix
    :param rx: copy rx-Frames (default: True)
    :param tx: copy tx-Frames (default: True)
    """
    # check whether ecu_or_glob is object or symbolic name
    if isinstance(ecu_or_glob, canmatrix.Ecu):
        ecu_list = [ecu_or_glob]
    else:
        ecu_list = source_db.glob_ecus(ecu_or_glob)

    for ecu in ecu_list:
        logger.info("Copying ECU " + ecu.name)
        copy_ecu(ecu, source_db, target_db)

        # copy tx-frames
        if tx is True:
            for frame in source_db.frames:
                if ecu.name in frame.transmitters:
                    copy_frame(frame.arbitration_id, source_db, target_db)

        # copy rx-frames
        if rx is True:
            for frame in source_db.frames:
                for signal in frame.signals:
                    if ecu.name in signal.receivers:
                        copy_frame(frame.arbitration_id, source_db, target_db)
                        break

    target_db.update_ecu_list()

    if direct_ecu_only:
        # delete ecu-names if not direct in communication to ecu
        ecus_to_delete = []
        for ecu in target_db.ecus:
            if ecu not in ecu_list:  # ecu is not a wanted ecu
                found = False
                for frame in target_db.frames:
                    if ecu.name in frame.transmitters:
                        found = True  # ecu is a sender of a received frame
                if not found:
                    ecus_to_delete.append(ecu)
        for ecu in ecus_to_delete:
            target_db.del_ecu(ecu)

def copy_signal(signal_glob, source_db, target_db):
    # type: (str, canmatrix.CanMatrix, canmatrix.CanMatrix) -> None
    """
    Copy Signals identified by name from source CAN matrix to target CAN matrix.
    In target CanMatrix the signal is put without frame, just on top level.

    :param signal_glob: Signal glob pattern
    :param source_db: Source CAN matrix
    :param target_db: Destination CAN matrix
    """
    for frame in source_db.frames:
        for source_signal in frame.glob_signals(signal_glob):
            target_signal = copy.deepcopy(source_signal)
            target_db.add_signal(target_signal)

            for attribute in source_db.signal_defines:
                target_db.add_signal_defines(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.signal_defines[attribute].definition))
                target_db.add_define_default(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.signal_defines[attribute].defaultValue))
                # update enum data types if needed:
                if source_db.signal_defines[attribute].type == 'ENUM':
                    temp_attr = source_signal.attribute(attribute, db=source_db)
                    if temp_attr not in target_db.signal_defines[attribute].values:
                        target_db.signal_defines[attribute].values.append(copy.deepcopy(temp_attr))
                        target_db.signal_defines[attribute].update()
                # only default value exists in source but is different to default value in target
                if attribute not in source_signal.attributes and source_signal.attribute(attribute, source_db) is not None and \
                    source_signal.attribute(attribute, source_db) != source_signal.attribute(attribute, target_db):
                    target_signal.add_attribute(attribute, source_signal.attribute(attribute, source_db))




def copy_frame(frame_id, source_db, target_db):
    # type: (canmatrix.ArbitrationId, canmatrix.CanMatrix, canmatrix.CanMatrix) -> bool
    """
    Copy a Frame identified by ArbitrationId from source CAN matrix to target CAN matrix.
    This function additionally copy all relevant ECUs and Defines.

    :param frame_id: Frame arbitration od
    :param source_db: Source CAN matrix
    :param target_db: Destination CAN matrix
    """
    frame_list = [source_db.frame_by_id(frame_id)]

    for frame in frame_list:
        logger.info("Copying Frame " + frame.name)

        if target_db.frame_by_id(frame.arbitration_id) is not None:
            # frame already in target_db...
            return False

        # copy Frame-Object:
        target_db.add_frame(copy.deepcopy(frame))

        # ECUs:
        # each transmitter of Frame could be ECU that is not listed already
        for transmitter in frame.transmitters:
            target_ecu = target_db.ecu_by_name(transmitter)
            source_ecu = source_db.ecu_by_name(transmitter)
            if source_ecu is not None and target_ecu is None:
                copy_ecu(source_ecu, source_db, target_db)

        # trigger all signals of Frame
        for sig in frame.signals:
            # each receiver of Signal could be ECU that is not listed already
            for receiver in sig.receivers:
                target_ecu = target_db.ecu_by_name(receiver)
                source_ecu = source_db.ecu_by_name(receiver)
                if source_ecu is not None and target_ecu is None:
                    copy_ecu(source_ecu, source_db, target_db)

        # copy all frame-defines
        for attribute in source_db.frame_defines:
            if frame.attribute(attribute, source_db) is None:
                continue
            if attribute not in target_db.frame_defines:
                target_db.add_frame_defines(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.frame_defines[attribute].definition))
                target_db.add_define_default(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.frame_defines[attribute].defaultValue))
            # only default value exists in source but is different to default value in target
            if attribute not in frame.attributes and frame.attribute(attribute, source_db) is not None and \
                    frame.attribute(attribute, source_db) != frame.attribute(attribute, target_db):
                target_db.frame_by_id(frame.arbitration_id).add_attribute(attribute, frame.attribute(attribute, source_db))
            # update enum data types if needed:
            if source_db.frame_defines[attribute].type == 'ENUM':
                temp_attr = frame.attribute(attribute, db=source_db)
                if temp_attr not in target_db.frame_defines[attribute].values:
                    target_db.frame_defines[attribute].values.append(copy.deepcopy(temp_attr))
                    target_db.frame_defines[attribute].update()

        # trigger all signals of Frame
        for sig in frame.signals:
            # delete all 'unknown' attributes
            for attribute in source_db.signal_defines:
                if sig.attribute(attribute, source_db) is None:
                    continue
                target_db.add_signal_defines(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.signal_defines[attribute].definition))
                target_db.add_define_default(
                    copy.deepcopy(attribute), copy.deepcopy(source_db.signal_defines[attribute].defaultValue))
                # update enum data types if needed:
                if source_db.signal_defines[attribute].type == 'ENUM':
                    temp_attr = sig.attribute(attribute, db=source_db)
                    if temp_attr not in target_db.signal_defines[attribute].values:
                        target_db.signal_defines[attribute].values.append(copy.deepcopy(temp_attr))
                        target_db.signal_defines[attribute].update()
                # only default value exists in source but is different to default value in target
                if attribute not in sig.attributes and sig.attribute(attribute, source_db) is not None and \
                    sig.attribute(attribute, source_db) != sig.attribute(attribute, target_db):
                    target_db.frame_by_id(frame.arbitration_id).signal_by_name(sig.name).add_attribute(attribute, sig.attribute(attribute, source_db))

    return True
