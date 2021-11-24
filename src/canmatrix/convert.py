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
import sys
import typing
from builtins import *

import canmatrix
import canmatrix.copy
import canmatrix.formats
import canmatrix.log

logger = logging.getLogger(__name__)
sys.path.append('..')  # todo remove?


def convert_pdu_container_to_multiplexed(frame):  # type: (canmatrix.Frame) -> canmatrix.Frame
    new_frame = copy.deepcopy(frame)
    if not frame.is_pdu_container:
        return new_frame
    header_id_signal = new_frame.signal_by_name("Header_ID")
    header_dlc_signal = new_frame.signal_by_name("Header_DLC")
    if header_id_signal is not None and header_dlc_signal is not None:
        header_id_signal.multiplex_setter("Multiplexor")
        bit_offset = header_id_signal.size + header_dlc_signal.size
    else:
        bit_offset = 0
    for sg_id, pdu in enumerate(new_frame.pdus):
        mux_val = pdu.id
        signal_group = []
        for signal in pdu.signals:
            signal.multiplex_setter(mux_val)
            signal.start_bit += bit_offset
            signal_group.append(signal.name)
            new_frame.add_signal(signal)
        signal_group_name = pdu.name
        if len(signal_group_name) == 0:
            signal_group_name = "HEARDER_ID_" + str(mux_val)
        new_frame.add_signal_group(signal_group_name, sg_id + 1, signal_group)
    new_frame.pdus = []
    return new_frame


def convert(infile, out_file_name, **options):  # type: (str, str, **str) -> None
    logger.info("Importing " + infile + " ... ")
    dbs = canmatrix.formats.loadp(infile, **options)
    logger.info("done\n")

    logger.info("Exporting " + out_file_name + " ... ")

    out_dbs = {}  # type: typing.Dict[str, canmatrix.CanMatrix]
    for name in dbs:
        db = None

        if options.get('ecus', False):
            ecu_list = options['ecus'].split(',')
            db = canmatrix.CanMatrix()
            direction = None
            for ecu in ecu_list:
                if ":" in ecu:
                    ecu, direction = ecu.split(":")
                canmatrix.copy.copy_ecu_with_frames(ecu, dbs[name], db, rx=(direction != "tx"), tx=(direction != "rx"))
        if options.get('frames', False):
            frame_list = options['frames'].split(',')
            db = canmatrix.CanMatrix() if db is None else db
            for frame_name in frame_list:
                frame_to_copy = dbs[name].frame_by_name(frame_name)
                canmatrix.copy.copy_frame(frame_to_copy.arbitration_id, dbs[name], db)
        if options.get('signals', False):
            signal_list = options['signals'].split(',')
            db = canmatrix.CanMatrix() if db is None else db
            for signal_name in signal_list:
                canmatrix.copy.copy_signal(signal_name, dbs[name], db)

        if db is None:
            db = dbs[name]

        if 'merge' in options and options['merge'] is not None:
            merge_files = options['merge'].split(',')
            for database in merge_files:
                merge_string = database.split(':')
                db_temp_list = canmatrix.formats.loadp(merge_string[0])
                for dbTemp in db_temp_list:
                    if merge_string.__len__() == 1:
                        print("merge complete: " + merge_string[0])
                        db.merge([db_temp_list[dbTemp]])
                        # for frame in db_temp_list[dbTemp].frames:
                        #    copyResult = canmatrix.copy.copy_frame(frame.id, db_temp_list[dbTemp], db)
                        #    if copyResult == False:
                        #        logger.error("ID Conflict, could not copy/merge frame " + frame.name + "  %xh " % frame.id + database)
                    for mergeOpt in merge_string[1:]:
                        if mergeOpt.split('=')[0] == "ecu":
                            canmatrix.copy.copy_ecu_with_frames(
                                mergeOpt.split('=')[1], db_temp_list[dbTemp], db)
                        if mergeOpt.split('=')[0] == "frame":
                            frame_to_copy = db_temp_list[name].frame_by_name(mergeOpt.split('=')[1])
                            canmatrix.copy.copy_frame(frame_to_copy.arbitration_id, db_temp_list[dbTemp], db)

        if 'renameEcu' in options and options['renameEcu'] is not None:
            rename_tuples = options['renameEcu'].split(',')
            for renameTuple in rename_tuples:
                old, new = renameTuple.split(':')
                db.rename_ecu(old, new)
        if 'deleteEcu' in options and options['deleteEcu'] is not None:
            delete_ecu_list = options['deleteEcu'].split(',')
            for ecu in delete_ecu_list:
                db.del_ecu(ecu)
        if 'renameFrame' in options and options['renameFrame'] is not None:
            rename_tuples = options['renameFrame'].split(',')
            for renameTuple in rename_tuples:
                old, new = renameTuple.split(':')
                db.rename_frame(old, new)
        if 'deleteFrame' in options and options['deleteFrame'] is not None:
            delete_frame_names = options['deleteFrame'].split(',')
            for frame_name in delete_frame_names:
                db.del_frame(frame_name)
        if 'addFrameReceiver' in options and options['addFrameReceiver'] is not None:
            touples = options['addFrameReceiver'].split(',')
            for touple in touples:
                (frameName, ecu) = touple.split(':')
                frames = db.glob_frames(frameName)
                for frame in frames:
                    for signal in frame.signals:
                        signal.add_receiver(ecu)
                    frame.update_receiver()

        if 'frameIdIncrement' in options and options['frameIdIncrement'] is not None:
            id_increment = int(options['frameIdIncrement'])
            for frame in db.frames:
                frame.arbitration_id.id += id_increment
        if 'changeFrameId' in options and options['changeFrameId'] is not None:
            change_tuples = options['changeFrameId'].split(',')
            for renameTuple in change_tuples:
                old, new = renameTuple.split(':')
                frame = db.frame_by_id(canmatrix.ArbitrationId(int(old)))
                if frame is not None:
                    frame.arbitration_id.id = int(new)
                else:
                    logger.error("frame with id {} not found", old)

        if 'setFrameFd' in options and options['setFrameFd'] is not None:
            fd_frame_list = options['setFrameFd'].split(',')
            for frame_name in fd_frame_list:
                frame_ptr = db.frame_by_name(frame_name)
                if frame_ptr is not None:
                    frame_ptr.is_fd = True
        if 'unsetFrameFd' in options and options['unsetFrameFd'] is not None:
            fd_frame_list = options['unsetFrameFd'].split(',')
            for frame_name in fd_frame_list:
                frame_ptr = db.frame_by_name(frame_name)
                if frame_ptr is not None:
                    frame_ptr.is_fd = False
                    frame_ptr.del_attribute("VFrameFormat")

        if 'skipLongDlc' in options and options['skipLongDlc'] is not None:
            delete_frame_list = [
                frame
                for frame in db.frames
                if frame.size > int(options['skipLongDlc'])
            ]
            for frame in delete_frame_list:
                db.del_frame(frame)

        if 'cutLongFrames' in options and options['cutLongFrames'] is not None:
            for frame in db.frames:
                if frame.size > int(options['cutLongFrames']):
                    delete_signal_list = [
                        sig
                        for sig in frame.signals
                        if sig.get_startbit() + int(sig.size) > int(options['cutLongFrames'])*8
                    ]
                    for sig in delete_signal_list:
                        frame.signals.remove(sig)
                    frame.size = 0
                    frame.calc_dlc()

        if 'renameSignal' in options and options['renameSignal'] is not None:
            rename_tuples = options['renameSignal'].split(',')
            for renameTuple in rename_tuples:
                old, new = renameTuple.split(':')
                db.rename_signal(old, new)
        if 'deleteSignal' in options and options['deleteSignal'] is not None:
            delete_signal_names = options['deleteSignal'].split(',')
            for signal_name in delete_signal_names:
                db.del_signal(signal_name)

        if 'deleteZeroSignals' in options and options['deleteZeroSignals']:
            db.delete_zero_signals()

        if 'deleteSignalAttributes' in options and options[
                'deleteSignalAttributes']:
            unwanted_attributes = options['deleteSignalAttributes'].split(',')
            db.del_signal_attributes(unwanted_attributes)

        if 'deleteFrameAttributes' in options and options[
                'deleteFrameAttributes']:
            unwanted_attributes = options['deleteFrameAttributes'].split(',')
            db.del_frame_attributes(unwanted_attributes)

        if 'deleteObsoleteDefines' in options and options[
                'deleteObsoleteDefines']:
            db.delete_obsolete_defines()

        if 'deleteObsoleteEcus' in options and options[
                'deleteObsoleteEcus']:
            db.delete_obsolete_ecus()

        if 'recalcDLC' in options and options['recalcDLC']:
            db.recalc_dlc(options['recalcDLC'])

        # PDU contained frames handling
        frame_pdu_container_list = [
            frame
            for frame in db.frames
            if frame.is_pdu_container
        ]
        if options.get('ignorePduContainer'):
            for frame in frame_pdu_container_list:
                db.del_frame(frame)
        else:
            # convert PDU contained frames to multiplexed frame
            for frame in frame_pdu_container_list:
                logger.warning("%s converted to Multiplexed frame", frame.name)
                new_frame = convert_pdu_container_to_multiplexed(frame)
                db.del_frame(frame)
                db.add_frame(new_frame)

        if options.get('signalNameFromAttrib') is not None:
            for signal in [b for a in db for b in a.signals]:
                signal.name = signal.attributes.get(options.get('signalNameFromAttrib'), signal.name)

        # Max Signal Value Calculation , if max value is 0
        if options.get('calcSignalMax') is not None and options['calcSignalMax']:
            for signal in [b for a in db for b in a.signals]:
                if signal.max == 0 or signal.max is None:
                    signal.calc_max_for_none = True
                    signal.set_max(None)

        # Max Signal Value Calculation
        if options.get('recalcSignalMax') is not None and options['recalcSignalMax']:
            for signal in [b for a in db for b in a.signals]:
                signal.calc_max_for_none = True
                signal.set_max(None)

        # Delete Unassigned Signals to a Valid Frame/Message
        if options.get('deleteFloatingSignals') is not None and options['deleteFloatingSignals']:
            for frame in db.frames:
                if frame.name == 'VECTOR__INDEPENDENT_SIG_MSG':
                    for signal in frame:
                        db.del_signal(signal)
                        logger.info("Deleted %s",(frame.name+"::"+signal.name))
                    db.del_frame(frame)

        # Check & Warn for Receiver Node against signals
        if options.get('checkSignalReceiver') is not None and options['checkSignalReceiver']:
            for frame in db.frames:
                for signal in frame:
                    if len(signal.receivers) == 0:
                        logger.warning("Please add Receiver for the signal %s ",(frame.name+"::"+signal.name))

        # Check & Warn Unassigned Signals to a Valid Frame/Message
        if options.get('checkFloatingSignals') is not None and options['checkFloatingSignals']:
            for frame in db.frames:
                if frame.name == 'VECTOR__INDEPENDENT_SIG_MSG':
                    for signal in frame:
                        logger.warning("Please map the signal %s to a valid frame or delete by deleteFloatingSignals", signal.name)

        # Check & Warn for Frame/Messages without Transmitter Node
        if options.get('checkFloatingFrames') is not None and options['checkFloatingFrames']:
            for frame in db.frames:
                if len(frame.transmitters) is 0:
                    logger.warning("No Transmitter Node Found for Frame %s", frame.name)

        # Check & Warn for Signals with Min/Max set to 0
        if options.get('checkSignalRange') is not None and options['checkSignalRange']:
            for frame in db.frames:
                for signal in frame.signals:
                    if (signal.phys2raw(signal.max) - signal.phys2raw(signal.min)) is 0:
                        logger.warning("Invalid Min , Max value of %s", (frame.name+"::"+signal.name))

        # Check for Signals without unit and Value table , the idea is to improve signal readability
        if options.get('checkSignalUnit') is not None and options['checkSignalUnit']:
            for frame in db.frames:
                for signal in frame:
                    if signal.unit is "" and len(signal.values) == 0:
                        logger.warning("Please add value table for the signal %s or add appropriate Unit", (frame.name+"::"+signal.name))

        # Convert dbc from J1939 to Extended format
        if options.get('convertToExtended') is not None and options['convertToExtended']:
            for frame in db.frames:
                frame.is_j1939=False
            db.add_attribute("ProtocolType","ExtendedCAN")

        # Convert dbc from Extended to J1939 format
        if options.get('convertToJ1939') is not None and options['convertToJ1939']:
            for frame in db.frames:
                frame.is_j1939=True
            db.add_attribute("ProtocolType","J1939")

        logger.info(name)
        logger.info("%d Frames found" % (db.frames.__len__()))

        out_dbs[name] = db

    if 'force_output' in options and options['force_output'] is not None:
        canmatrix.formats.dumpp(out_dbs, out_file_name, export_type=options[
                                'force_output'], **options)
    else:
        canmatrix.formats.dumpp(out_dbs, out_file_name, **options)
    logger.info("done")
