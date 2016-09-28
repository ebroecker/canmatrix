#!/usr/bin/env python3

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

from __future__ import print_function
from __future__ import absolute_import

from .log import setup_logger, set_log_level
logger = setup_logger('root')
import sys
import os
sys.path.append('..')
import canmatrix.formats
import canmatrix.canmatrix as cm
import canmatrix.copy as cmcp


def convert(infile, outfileName, **options):
    dbs = {}

    logger.info("Importing " + infile + " ... ")
    dbs = canmatrix.formats.loadp(infile, **options)
    logger.info("done\n")

    logger.info("Exporting " + outfileName + " ... ")

    outdbs = {}
    for name in dbs:
        db = None

        if 'ecus' in options and options['ecus'] is not None:
            ecuList = options['ecus'].split(',')
            db = cm.CanMatrix()
            for ecu in ecuList:
                logger.info("Copying ECU " + ecu)
                cmcp.copyBUwithFrames(ecu, dbs[name], db)
        if 'frames' in options and options['frames'] is not None:
            frameList = options['frames'].split(',')
            db = cm.CanMatrix()
            for frame in frameList:
                logger.info("Copying Frame " + frame)
                cmcp.copyFrame(frame, dbs[name], db)
        if db is None:
            db = dbs[name]

        if 'merge' in options and options['merge'] is not None:
            mergeFiles = options['merge'].split(',')
            for database in mergeFiles:
                mergeString = database.split(':')
                dbTempList = canmatrix.formats.loadp(mergeString[0])
                for dbTemp in dbTempList:
                    if mergeString.__len__() == 1:
                        print ("merge complete: " + mergeString[0])
                        for frame in dbTempList[dbTemp].frames:
                            cmcp.copyFrame(frame.id, dbTempList[dbTemp], db)
                    for mergeOpt in mergeString[1:]:
                        if mergeOpt.split('=')[0] == "ecu":
                            cmcp.copyBUwithFrames(
                                mergeOpt.split('=')[1], dbTempList[dbTemp], db)
                        if mergeOpt.split('=')[0] == "frame":
                            cmcp.copyFrame(
                                mergeOpt.split('=')[1], dbTempList[dbTemp], db)

        if 'renameEcu' in options and options['renameEcu'] is not None:
            renameTuples = options['renameEcu'].split(',')
            for renameTuple in renameTuples:
                old, new = renameTuple.split(':')
                db.renameEcu(old, new)
        if 'deleteEcu' in options and options['deleteEcu'] is not None:
            deleteEcuList = options['deleteEcu'].split(',')
            for ecu in deleteEcuList:
                db.delEcu(ecu)
        if 'renameFrame' in options and options['renameFrame'] is not None:
            renameTuples = options['renameFrame'].split(',')
            for renameTuple in renameTuples:
                old, new = renameTuple.split(':')
                db.renameFrame(old, new)
        if 'deleteFrame' in options and options['deleteFrame'] is not None:
            deleteFrameList = options['deleteFrame'].split(',')
            for frame in deleteFrameList:
                db.delFrame(frame)
        if 'renameSignal' in options and options['renameSignal'] is not None:
            renameTuples = options['renameSignal'].split(',')
            for renameTuple in renameTuples:
                old, new = renameTuple.split(':')
                db.renameSignal(old, new)
        if 'deleteSignal' in options and options['deleteSignal'] is not None:
            deleteSignalList = options['deleteSignal'].split(',')
            for signal in deleteSignalList:
                db.delSignal(signal)

        if 'deleteZeroSignals' in options and options['deleteZeroSignals']:
            db.deleteZeroSignals()

        if 'deleteSignalAttributes' in options and options[
                'deleteSignalAttributes']:
            unwantedAttributes = options['deleteSignalAttributes'].split(',')
            db.delSignalAttributes(unwantedAttributes)

        if 'deleteFrameAttributes' in options and options[
                'deleteFrameAttributes']:
            unwantedAttributes = options['deleteFrameAttributes'].split(',')
            db.delFrameAttributes(unwantedAttributes)

        if 'deleteObsoleteDefines' in options and options[
                'deleteObsoleteDefines']:
            db.deleteObsoleteDefines()

        if 'recalcDLC' in options and options['recalcDLC']:
            db.recalcDLC(options['recalcDLC'])

        logger.info(name)
        logger.info("%d Frames found" % (db.frames.__len__()))

        outdbs[name] = db

    if 'force_output' in options and options['force_output'] is not None:
        canmatrix.formats.dumpp(outdbs, outfileName, exportType=options[
                                'force_output'], **options)
    else:
        canmatrix.formats.dumpp(outdbs, outfileName, **options)
    logger.info("done")


def main():
    from optparse import OptionParser

    usage = """
    %prog [options] import-file export-file

    import-file: *.dbc|*.dbf|*.kcd|*.arxml|*.json|*.xls(x)|*.sym
    export-file: *.dbc|*.dbf|*.kcd|*.arxml|*.json|*.xls(x)|*.sym

    followig formats are availible at this installation:
    \n"""

    for suppFormat, features in canmatrix.formats.supportedFormats.items():
        usage += suppFormat + "\t"
        if 'load' in features:
            usage += "import"
        usage += "\t"
        if 'dump' in features:
            usage += "export"
        usage += "\n"

    parser = OptionParser(usage=usage)
    # parser.add_option("-d", "--debug",
    #                  dest="debug", default=False,
    #                  help="print debug messages to stdout")

    parser.add_option(
        "-v",
        dest="verbosity",
        action="count",
        help="Output verbosity",
        default=0)
    parser.add_option(
        "-s",
        dest="silent",
        action="store_true",
        help="don't print status messages to stdout. (only errors)",
        default=False)
    parser.add_option(
        "-f",
        dest="force_output",
        help="enforce output format, ignoring output file extension (e.g., -f csv")
    parser.add_option("", "--deleteZeroSignals", action="store_true",
                      dest="deleteZeroSignals", default=False,
                      help="delete zero length signals (signals with 0 bit length) from matrix\ndefault False")
    parser.add_option("", "--deleteSignalAttributes",
                      dest="deleteSignalAttributes", default=None,
                      help="delete attributes from all signals\nExample --deleteSignalAttributes GenMsgCycle,CycleTime")
    parser.add_option("", "--deleteFrameAttributes",
                      dest="deleteFrameAttributes", default=None,
                      help="delete attributes from all frames\nExample --deleteFrameAttributes GenMsgCycle,CycleTime")
    parser.add_option("", "--deleteObsoleteDefines", action="store_true",
                      dest="deleteObsoleteDefines", default=False,
                      help="delete defines from all Boardunits, frames and Signals\nExample --deleteObsoleteDefines")
    parser.add_option("", "--recalcDLC",
                      dest="recalcDLC", default=False,
                      help="recalculate dlc; max: use maximum of stored and calculated dlc; force: force new calculated dlc")

    parser.add_option("", "--arxmlIgnoreClusterInfo", action="store_true",
                      dest="arxmlIgnoreClusterInfo", default=False,
                      help="Ignore any can cluster info from arxml; Import all frames in one matrix\ndefault 0")
    parser.add_option("", "--arxmlExportVersion",
                      dest="arVersion", default="3.2.3",
                      help="Set output AUTOSAR version\ncurrently only 3.2.3 and 4.1.0 are supported\ndefault 3.2.3")

    parser.add_option("", "--dbcImportEncoding",
                      dest="dbcImportEncoding", default="iso-8859-1",
                      help="Import charset of dbc (relevant for units), maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--dbcImportCommentEncoding",
                      dest="dbcImportCommentEncoding", default="iso-8859-1",
                      help="Import charset of Comments in dbc\ndefault iso-8859-1")
    parser.add_option("", "--dbcExportEncoding",
                      dest="dbcExportEncoding", default="iso-8859-1",
                      help="Export charset of dbc (relevant for units), maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--dbcExportCommentEncoding",
                      dest="dbcExportCommentEncoding", default="iso-8859-1",
                      help="Export charset of comments in dbc\ndefault iso-8859-1")

    parser.add_option("", "--dbfImportEncoding",
                      dest="dbfImportEncoding", default="iso-8859-1",
                      help="Import charset of dbf, maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--dbfExportEncoding",
                      dest="dbfExportEncoding", default="iso-8859-1",
                      help="Export charset of dbf, maybe utf-8\ndefault iso-8859-1")

    parser.add_option("", "--symImportEncoding",
                      dest="symImportEncoding", default="iso-8859-1",
                      help="Import charset of sym format, maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--symExportEncoding",
                      dest="symExportEncoding", default="iso-8859-1",
                      help="Export charset of sym format, maybe utf-8\ndefault iso-8859-1")

    parser.add_option("", "--xlsMotorolaBitFormat",
                      dest="xlsMotorolaBitFormat", default="msbreverse",
                      help="Excel format for startbit of motorola codescharset signals\nValid values: msb, lsb, msbreverse\n default msbreverse")
    parser.add_option("", "--jsonExportCanard",
                      dest="jsonCanard", action="store_true", default=False,
                      help="Export Canard compatible json format")
    parser.add_option("", "--jsonExportAll",
                      dest="jsonAll", action="store_true", default=False,
                      help="Export more data to json format")

    parser.add_option("", "--ecus",
                      dest="ecus", default=None,
                      help="Copy only given ECUs (comma separated list) to target matrix")

    parser.add_option("", "--frames",
                      dest="frames", default=None,
                      help="Copy only given Frames (comma separated list) to target matrix")

    parser.add_option("", "--merge",
                      dest="merge", default=None,
                      help="merge additional can databases.\nSyntax: --merge filename[:ecu=SOMEECU][:frame=FRAME1][:frame=FRAME2],filename2")

    parser.add_option("", "--deleteEcu",
                      dest="deleteEcu", default=None,
                      help="delete Ecu form databases. (comma separated list)\nSyntax: --deleteEcu=myEcu,mySecondEcu")
    parser.add_option("", "--renameEcu",
                      dest="renameEcu", default=None,
                      help="rename Ecu form databases. (comma separated list)\nSyntax: --renameEcu=myOldEcu:myNewEcu,mySecondEcu:mySecondNewEcu")

    parser.add_option("", "--deleteFrame",
                      dest="deleteFrame", default=None,
                      help="delete Frame form databases. (comma separated list)\nSyntax: --deleteFrame=myFrame1,mySecondFrame")
    parser.add_option("", "--renameFrame",
                      dest="renameFrame", default=None,
                      help="rename Frame form databases. (comma separated list)\nSyntax: --renameFrame=myOldFrame:myNewFrame,mySecondFrame:mySecondNewFrame")

    parser.add_option("", "--deleteSignal",
                      dest="deleteSignal", default=None,
                      help="delete Signal form databases. (comma separated list)\nSyntax: --deleteSignal=mySignal1,mySecondSignal")
    parser.add_option("", "--renameSignal",
                      dest="renameSignal", default=None,
                      help="rename Signal form databases. (comma separated list)\nSyntax: --renameSignal=myOldSignal:myNewSignal,mySecondSignal:mySecondNewSignal")

    (cmdlineOptions, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    infile = args[0]
    outfileName = args[1]

    verbosity = cmdlineOptions.verbosity
    if cmdlineOptions.silent:
        # only print error messages, ignore verbosity flag
        verbosity = -1

    set_log_level(logger, verbosity)

    convert(infile, outfileName, **cmdlineOptions.__dict__)

if __name__ == '__main__':
    sys.exit(main())
