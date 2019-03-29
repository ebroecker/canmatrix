#!/usr/bin/env python3
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

from __future__ import absolute_import
from __future__ import print_function

import logging
import sys
import typing

import canmatrix.canmatrix as cm
import canmatrix.copy
import canmatrix.formats
import canmatrix.log

logger = logging.getLogger(__name__)
sys.path.append('..')  # todo remove?


def convert(infile, out_file_name, **options):  # type: (str, str, **str) -> None
    logger.info("Importing " + infile + " ... ")
    dbs = canmatrix.formats.loadp(infile, **options)
    logger.info("done\n")

    logger.info("Exporting " + out_file_name + " ... ")

    out_dbs = {}
    for name in dbs:
        db = None

        if 'ecus' in options and options['ecus'] is not None:
            ecu_list = options['ecus'].split(',')
            db = cm.CanMatrix()
            for ecu in ecu_list:
                canmatrix.copy.copy_ecu_with_frames(ecu, dbs[name], db)
        if 'frames' in options and options['frames'] is not None:
            frame_list = options['frames'].split(',')
            db = cm.CanMatrix()
            for frame_name in frame_list:  # type: str
                frame_to_copy = dbs[name].frame_by_name(frame_name)  # type: cm.Frame
                canmatrix.copy.copy_frame(frame_to_copy.arbitration_id, dbs[name], db)
        if options.get('signals', False):
            signal_list = options['signals'].split(',')
            db = cm.CanMatrix()
            for signal_name in signal_list:  # type: str
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
                            frame_to_copy = dbs[name].frame_by_name(mergeOpt.split('=')[1])
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
                for frame in frames:  # type: cm.Frame
                    for signal in frame.signals:  # type: cm.Signal
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
                frame = db.frame_by_id(cm.ArbitrationId(int(old)))
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

        if 'skipLongDlc' in options and options['skipLongDlc'] is not None:
            delete_frame_list = []  # type: typing.List[cm.Frame]
            for frame in db.frames:
                if frame.size > int(options['skipLongDlc']):
                    delete_frame_list.append(frame)
            for frame in delete_frame_list:
                db.del_frame(frame)

        if 'cutLongFrames' in options and options['cutLongFrames'] is not None:
            for frame in db.frames:
                if frame.size > int(options['cutLongFrames']):
                    delete_signal_list = []
                    for sig in frame.signals:
                        if sig.get_startbit() + int(sig.size) > int(options['cutLongFrames'])*8:
                            delete_signal_list.append(sig)
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

        if 'recalcDLC' in options and options['recalcDLC']:
            db.recalc_dlc(options['recalcDLC'])

        logger.info(name)
        logger.info("%d Frames found" % (db.frames.__len__()))

        out_dbs[name] = db

    if 'force_output' in options and options['force_output'] is not None:
        canmatrix.formats.dumpp(out_dbs, out_file_name, exportType=options[
                                'force_output'], **options)
    else:
        canmatrix.formats.dumpp(out_dbs, out_file_name, **options)
    logger.info("done")
