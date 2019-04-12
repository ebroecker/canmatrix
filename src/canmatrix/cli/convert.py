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

import canmatrix.convert

logger = logging.getLogger(__name__)


def main():  # type: () -> int
    canmatrix.log.setup_logger()
    from optparse import OptionParser

    usage = """
    %prog [options] import-file export-file

    import-file: *.dbc|*.dbf|*.kcd|*.arxml|*.json|*.xls(x)|*.sym
    export-file: *.dbc|*.dbf|*.kcd|*.arxml|*.json|*.xls(x)|*.sym

    following formats are available at this installation:
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
        default=1)
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
                      help="delete defines from all ECUs, frames and Signals\nExample --deleteObsoleteDefines")
    parser.add_option("", "--recalcDLC",
                      dest="recalcDLC", default=False,
                      help="recalculate dlc; max: use maximum of stored and calculated dlc; force: force new calculated dlc")
    parser.add_option("", "--skipLongDlc",
                      dest="skipLongDlc", default=None,
                      help="skip all Frames with dlc bigger than given threshold\n")
    parser.add_option("", "--cutLongFrames",
                      dest="cutLongFrames", default=None,
                      help="cut all signals out of Frames with dlc bigger than given threshold\n")



    parser.add_option("", "--arxmlIgnoreClusterInfo", action="store_true",
                      dest="arxmlIgnoreClusterInfo", default=False,
                      help="Ignore any can cluster info from arxml; Import all frames in one matrix\ndefault 0")

    parser.add_option("", "--arxmlUseXpath", action="store_true",
                      dest="arxmlUseXpath", default=False,
                      help="Use Xpath-Implementation for resolving AR-Paths; \ndefault False")


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
    parser.add_option("", "--jsonMotorolaBitFormat",
                      dest="jsonMotorolaBitFormat", default="lsb",
                      help="Json format: startbit of motorola signals\nValid values: msb, lsb, msbreverse\n default lsb")

    parser.add_option("", "--additionalFrameAttributes",
                      dest="additionalFrameAttributes", default="",
                      help="append columns to csv/xls(x), example: is_fd")

    parser.add_option("", "--additionalSignalAttributes",
                      dest="additionalAttributes", default="",
                      help="append columns to csv/xls(x), example: is_signed,attributes[\"GenSigStartValue\"] ")

    parser.add_option("", "--ecus",
                      dest="ecus", default=None,
                      help="Copy only given ECUs (comma separated list) to target matrix")

    parser.add_option("", "--frames",
                      dest="frames", default=None,
                      help="Copy only given Frames (comma separated list) to target matrix")

    parser.add_option("", "--signals",
                      dest="signals", default=None,
                      help="Copy only given Signals (comma separated list) to target matrix just as 'free' signals without containing frame")

    parser.add_option("", "--merge",
                      dest="merge", default=None,
                      help="merge additional can databases.\nSyntax: --merge filename[:ecu=SOMEECU][:frame=FRAME1][:frame=FRAME2],filename2")

    parser.add_option("", "--deleteEcu",
                      dest="deleteEcu", default=None,
                      help="delete Ecu form databases. (comma separated list)\nSyntax: --deleteEcu=myEcu,mySecondEcu")
    parser.add_option("", "--renameEcu",
                      dest="renameEcu", default=None,
                      help="rename Ecu form databases. (comma separated list)\nSyntax: --renameEcu=myOldEcu:myNewEcu,mySecondEcu:mySecondNewEcu")

    parser.add_option("", "--addFrameReceiver",
                      dest="addFrameReceiver", default=None,
                      help="add receiver Ecu to frame(s) (comma separated list)\nSyntax: --addFrameReceiver=framename:myNewEcu,mySecondEcu:myNEWEcu")



    parser.add_option("", "--deleteFrame",
                      dest="deleteFrame", default=None,
                      help="delete Frame form databases. (comma separated list)\nSyntax: --deleteFrame=myFrame1,mySecondFrame")
    parser.add_option("", "--renameFrame",
                      dest="renameFrame", default=None,
                      help="rename Frame form databases. (comma separated list)\nSyntax: --renameFrame=myOldFrame:myNewFrame,mySecondFrame:mySecondNewFrame")

    parser.add_option("", "--frameIdIncrement",
                      dest="frameIdIncrement", default=None,
                      help="increment each frame.id in database by increment\nSyntax: --frameIdIncrement=increment")

    parser.add_option("", "--changeFrameId",
                      dest="changeFrameId", default=None,
                      help="change frame.id in database\nSyntax: --changeFrameId=oldId:newId")


    parser.add_option("", "--deleteSignal",
                      dest="deleteSignal", default=None,
                      help="delete Signal form databases. (comma separated list)\nSyntax: --deleteSignal=mySignal1,mySecondSignal")
    parser.add_option("", "--renameSignal",
                      dest="renameSignal", default=None,
                      help="rename Signal form databases. (comma separated list)\nSyntax: --renameSignal=myOldSignal:myNewSignal,mySecondSignal:mySecondNewSignal")
    parser.add_option("", "--setFrameFd",
                      dest="setFrameFd", default=None,
                      help="set Frame from database to canfd. (comma separated list)\nSyntax: --setFrameFd=myFrame1,mySecondFrame")
    parser.add_option("", "--unsetFrameFd",
                      dest="unsetFrameFd", default=None,
                      help="set Frame from database to normal (not FD). (comma separated list)\nSyntax: --unsetFrameFd=myFrame1,mySecondFrame")

    (cmdlineOptions, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        return 1

    infile = args[0]
    out_file_name = args[1]

    verbosity = cmdlineOptions.verbosity
    if cmdlineOptions.silent:
        # only print error messages, ignore verbosity flag
        verbosity = -1

    canmatrix.log.set_log_level(logger, verbosity)

    canmatrix.convert.convert(infile, out_file_name, **cmdlineOptions.__dict__)
    return 0


if __name__ == '__main__':
    sys.exit(main())
