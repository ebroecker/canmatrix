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

from __future__ import absolute_import, division, print_function

import logging
import sys

import click

import canmatrix.convert
import canmatrix.log

logger = logging.getLogger(__name__)


def get_formats():
    input = ""
    output = ""
    for suppFormat, features in canmatrix.formats.supportedFormats.items():
        if 'load' in features:
            input += suppFormat + "\n"
        if 'dump' in features:
            output += suppFormat + "\n"
    return (input, output)


@click.command()
# global switches
@click.option('-v', '--verbose', 'verbosity', count=True, default=1)
@click.option('-s', '--silent/--no-silent', is_flag=True, default=False, help="don't print status messages to stdout. (only errors)")
@click.option('-f', '--force_output', help="enforce output format, ignoring output file extension (e.g., -f csv).\nSupported formats for writing:\n" + get_formats()[1])
@click.option('-i', '--input_format', 'import_type', help="give hint for input format\nSupported formats for reading:\n" + get_formats()[0])
@click.option('--ignoreEncodingErrors/--no-ignoreEncodingErrors', 'ignoreEncodingErrors', default=False, help="ignore character encoding errors during export (dbc,dbf,sym)")
# manipulation and filter switches
@click.option('--deleteObsoleteDefines/--no-deleteObsoleteDefines', 'deleteObsoleteDefines', default=False, help="delete defines from all ECUs, frames and Signals\nExample --deleteObsoleteDefines")
@click.option('--deleteEcu', 'deleteEcu', help="delete Ecu form databases. (comma separated list)\nSyntax: --deleteEcu=myEcu,mySecondEcu")
@click.option('--deleteObsoleteEcus/--no-deleteObsoleteEcus', 'deleteObsoleteEcus', default=False, help="delete ECUs which are not references as transmitter or receiver\nExample --deleteObsoleteEcus")
@click.option('--renameEcu', 'renameEcu', help="rename Ecu form databases. (comma separated list)\nSyntax: --renameEcu=myOldEcu:myNewEcu,mySecondEcu:mySecondNewEcu")
@click.option('--deleteSignal', 'deleteSignal', help="delete Signal form databases. (comma separated list)\nSyntax: --deleteSignal=mySignal1,mySecondSignal")
@click.option('--renameSignal', 'renameSignal', help="rename Signal form databases. (comma separated list)\nSyntax: --renameSignal=myOldSignal:myNewSignal,mySecondSignal:mySecondNewSignal")
@click.option('--signalNameFromAttrib', 'signalNameFromAttrib', help="change signal_name to given signal attribute\n\
Example --signalNameFromAttrib SysSignalName\nARXML known Attributes: SysSignalName, ISignalName, CompuMethodName", default=None)
@click.option('--deleteZeroSignals/--no-deleteZeroSignals', 'deleteZeroSignals', default=False, help="delete zero length signals (signals with 0 bit length) from matrix\ndefault False")
@click.option('--deleteSignalAttributes', 'deleteSignalAttributes', help="delete attributes from all signals\nExample --deleteSignalAttributes GenMsgSomeVar,CycleTime")
@click.option('--deleteFrame', 'deleteFrame', help="delete Frame form databases. (comma separated list)\nSyntax: --deleteFrame=myFrame1,mySecondFrame")
@click.option('--renameFrame', 'renameFrame', help="increment each frame.id in database by increment\nSyntax: --frameIdIncrement=increment")
@click.option('--addFrameReceiver', 'addFrameReceiver', help="add receiver Ecu to frame(s) (comma separated list)\nSyntax: --addFrameReceiver=framename:myNewEcu,mySecondEcu:myNEWEcu")
@click.option('--changeFrameId', 'changeFrameId', help="change frame.id in database\nSyntax: --changeFrameId=oldId:newId")
@click.option('--setFrameFd', 'setFrameFd', help="set Frame from database to canfd. (comma separated list)\nSyntax: --setFrameFd=myFrame1,mySecondFrame")
@click.option('--unsetFrameFd', 'unsetFrameFd', help="set Frame from database to normal (not FD). (comma separated list)\nSyntax: --unsetFrameFd=myFrame1,mySecondFrame")
@click.option('--recalcDLC', 'recalcDLC', help="recalculate dlc; max: use maximum of stored and calculated dlc; force: force new calculated dlc")
@click.option('--skipLongDlc', 'skipLongDlc', help="skip all Frames with dlc bigger than given threshold")
@click.option('--cutLongFrames',  'cutLongFrames', help="cut all signals out of Frames with dlc bigger than given threshold")
@click.option('--deleteFrameAttributes', 'deleteFrameAttributes', help="delete attributes from all frames\nExample --deleteFrameAttributes GenMsgSomeVar,CycleTime")
@click.option('--ecus', help="Copy only given ECUs (comma separated list) to target matrix; suffix 'rx' or 'tx' for selection: Example: --ecus FirstEcu:rx,SecondEcu:tx,ThirdEcu")
@click.option('--frames', help="Copy only given Frames (comma separated list) to target matrix")
@click.option('--signals', help="Copy only given Signals (comma separated list) to target matrix just as 'free' signals without containing frame")
@click.option('--merge', help="merge additional can databases.\nSyntax: --merge filename[:ecu=SOMEECU][:frame=FRAME1][:frame=FRAME2],filename2")
@click.option('--ignorePduContainer/--no-ignorePduContainer', 'ignorePduContainer', default = False, help="Ignore any Frame with PDU container; if no export as multiplexed Frames\ndefault False")
@click.option('--calcSignalMax/--no-calcSignalMax', 'calcSignalMax', default = False, help="Calculate Signals Maximum Physical Value; If maximum value is set to 0\ndefault False")
@click.option('--recalcSignalMax/--no-recalcSignalMax', 'recalcSignalMax', default = False, help="Recalculate Signals Maximum Physical Value for the entire database\ndefault False")
@click.option('--deleteFloatingSignals/--no-deleteFloatingSignals', 'deleteFloatingSignals', default = False, help="if deleteFloatingSignals is set , then unassigned signals to a frame/message will be deleted \tdefault: False")

#Frame/Signal Check switches
@click.option('--checkFloatingFrames/--no-checkFloatingFrames', 'checkFloatingFrames', default = False, help="if checkFloatingFrames is set, CAN message/frame without sender node will be warned .\tdefault: False")
@click.option('--checkSignalRange/--no-checkSignalRange', 'checkSignalRange', default = False, help="if checkSignalRange is set, then signals consisting raw min/max value set to 0 will be warned. \tdefault: False ")
@click.option('--checkSignalUnit/--no-checkSignalUnit', 'checkSignalUnit', default = False, help="if checkSignalUnit is set , then signals without units and value table will be warned. \tdefault: False")
@click.option('--checkSignalReceiver/--no-checkSignalReceiver', 'checkSignalReceiver', default = False, help="if checkSignalReceiver is set, then signals without an assigned Receiver will be warned \tdefault: False")
@click.option('--checkFloatingSignals/--no-checkFloatingSignals', 'checkFloatingSignals', default = False, help="if checkFloatingSignals is set, then unassigned signals to a frame/message will be warned \tdefault: False")


# arxml switches
@click.option('--arxmlIgnoreClusterInfo/--no-arxmlIgnoreClusterInfo', 'arxmlIgnoreClusterInfo', default=False, help="Ignore any can cluster info from arxml; Import all frames in one matrix\ndefault False")
@click.option('--arxmlExportVersion', 'arVersion',  default="3.2.3", help="Set output AUTOSAR version\ncurrently only 3.2.3 and 4.1.0 are supported\ndefault 3.2.3")
@click.option('--arxmlFlexray/--no-arxmlFlexray', 'decode_flexray', default = False, help="EXPERIMENTAL: import basic flexray data from ARXML")
@click.option('--arxmlEthernet/--no-arxmlEthernet', 'decode_ethernet', default = False, help="EXPERIMENTAL: import basic ethernet data from ARXML")


# dbc switches
@click.option('--dbcImportEncoding', 'dbcImportEncoding', default="iso-8859-1", help="Import charset of dbc (relevant for units), maybe utf-8\ndefault iso-8859-1")
@click.option('--dbcImportCommentEncoding', 'dbcImportCommentEncoding', default="iso-8859-1", help="Import charset of Comments in dbc\ndefault iso-8859-1")
@click.option('--dbcExportEncoding', 'dbcExportEncoding', default="iso-8859-1", help="Export charset of dbc (relevant for units), maybe utf-8\ndefault iso-8859-1")
@click.option('--dbcExportCommentEncoding', 'dbcExportCommentEncoding', default="iso-8859-1", help="Export charset of comments in dbc\ndefault iso-8859-1")
@click.option('--dbcUniqueSignalNames/--no-dbcUniqueSignalNames', 'dbcUniqueSignalNames', default=True, help="Check if signal names are unique per frame")
@click.option('--convertToExtended/--no-convertToExtended', 'convertToExtended', default = False, help="if convertToExtended is set , then the canmatrix will convert the dbc to extended format \tdefault: False")
@click.option('--convertToJ1939/--no-convertToJ1939', 'convertToJ1939', default = False, help="if convertToJ1939 is set , then the canmatrix will convert the dbc to J1939 format \tdefault: False")

# dbf switches
@click.option('--dbfImportEncoding', 'dbfImportEncoding', default="iso-8859-1", help="Import charset of dbf, maybe utf-8\ndefault iso-8859-1")
@click.option('--dbfExportEncoding', 'dbfExportEncoding', default="iso-8859-1", help="Export charset of dbf, maybe utf-8\ndefault iso-8859-1")
# sym switches
@click.option('--symImportEncoding', 'symImportEncoding', default="iso-8859-1", help="Import charset of sym format, maybe utf-8\ndefault iso-8859-1")
@click.option('--symExportEncoding', 'symExportEncoding', default="iso-8859-1", help="Export charset of sym format, maybe utf-8\ndefault iso-8859-1")
# xls/csv switches
@click.option('--xlsMotorolaBitFormat', 'xlsMotorolaBitFormat', default="msbreverse", help="Excel format for startbit of motorola codescharset signals\nValid values: msb, lsb, msbreverse\n default msbreverse")
@click.option('--additionalFrameAttributes', 'additionalFrameAttributes', default="", help="append columns to csv/xls(x), example: is_fd")
@click.option('--additionalSignalAttributes', 'additionalSignalAttributes', default="", help="append columns to csv/xls(x), example: is_signed,attributes[\"GenSigStartValue\"]")
@click.option('--xlsValuesInSeperateLines/--no-xlsValuesInSeperateLines', 'xlsValuesInSeperateLines', default = False, help="Excel format: create seperate line for each value of signal value table\tdefault: False")
# json switches
@click.option('--jsonExportCanard/--no-jsonExportCanard', 'jsonExportCanard', default=False, help="Export Canard compatible json format")
@click.option('--jsonExportAll/--no-jsonExportAll', 'jsonExportAll', default=False, help="Export more data to json format")
@click.option('--jsonMotorolaBitFormat', 'jsonMotorolaBitFormat', default="lsb", help="Json format: startbit of motorola signals\nValid values: msb, lsb, msbreverse\n default lsb")
@click.option('--jsonNativeTypes/--no-jsonNativeTypes', 'jsonNativeTypes', default=False, help="Uses native json representation for decimals instead of string.")
#sym switches
@click.option('--symExportEncoding', 'symExportEncoding', default="iso-8859-1", help="Export charset of sym format, maybe utf-8\ndefault iso-8859-1")
# in and out file
@click.argument('infile', required=True)
@click.argument('outfile', required=True)
#
def cli_convert(infile, outfile, silent, verbosity, **options):
    """
    canmatrix.cli.convert [options] import-file export-file

    import-file: *.dbc|*.dbf|*.kcd|*.arxml|*.json|*.xls(x)|*.sym
    export-file: *.dbc|*.dbf|*.kcd|*.arxml|*.json|*.xls(x)|*.sym|*.py

    \n"""

    root_logger = canmatrix.log.setup_logger()

    if silent is True:
        # only print error messages, ignore verbosity flag
        verbosity = -1
        options["silent"] = True

    canmatrix.log.set_log_level(root_logger, verbosity)
    if options["ignoreEncodingErrors"]:
        options["ignoreEncodingErrors"] = "ignore"
    else:
        options["ignoreEncodingErrors"] = "strict"

    canmatrix.convert.convert(infile, outfile, **options)
    return 0


if __name__ == '__main__':
    sys.exit(cli_convert())
