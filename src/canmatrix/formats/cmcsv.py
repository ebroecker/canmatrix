#!/usr/bin/env python
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

#
# this script exports canmatrix-objects to a CSV file. (Based on xlsx)
# Author: Martin Hoffmann (m8ddin@gmail.com)

from __future__ import absolute_import

import collections
import csv
import logging
import sys
import typing

import canmatrix.formats.xls_common

logger = logging.getLogger(__name__)
CsvDataType = typing.Union[str, int]

extension = 'csv'


class CsvRow:
    def __init__(self):  # type: () -> None
        self._row_dict = collections.defaultdict(str)  # type: typing.Dict[int, CsvDataType]

    def __getitem__(self, key):  # type: (int) -> CsvDataType
        return self._row_dict[key]

    def __setitem__(self, key, item):  # type: (int, CsvDataType) -> None
        if sys.version_info <= (3, 0):
            if type(item).__name__ == "unicode":
                item = item.encode('utf-8')
        self._row_dict[key] = item

    def __add__(self, other):  # type: (typing.Iterable[CsvDataType]) -> CsvRow
        if len(self._row_dict.keys()) > 0:
            start = max(self._row_dict.keys()) + 1
        else:
            start = 0
        i = 0
        for item in other:
            self[start + i] = item
            i += 1
        return self

    def write(self, column, value):  # type: (int, CsvDataType) -> None
        self._row_dict[column] = value

    @property
    def as_list(self):  # type: () -> typing.List[str]
        # Generate list of single cells in the row till highest index (dictionary key)
        # Empty cells (non-existent keys) are generated as empty string
        return [str(self._row_dict[x])
                for x in range(0, max(self._row_dict) + 1)]

    def to_csv(self, delimiter=','):  # type: (str) -> str
        text = delimiter.join(self.as_list)
        return text.replace('\n', ' ')

    def __str__(self):  # type: () -> str
        return self.to_csv()


def write_ecu_matrix(ecu_name_list, sig, frame, row, col):
    # type: (typing.Sequence[str], canmatrix.Signal, canmatrix.Frame, CsvRow, int) -> int
    # iterate over ecus:
    for ecu_name in ecu_name_list:
        # write "s" "r" "r/s" if signal is sent, received or send and received by ECU
        if ecu_name in sig.receivers and ecu_name in frame.transmitters:
            row[col] = "r/s"
        elif ecu_name in sig.receivers:
            row[col] = "r"
        elif ecu_name in frame.transmitters:
            row[col] = "s"
        else:
            pass
        col += 1
    return col


def dump(db, file_object, delimiter=',', **options):
    # type: (canmatrix.CanMatrix, typing.BinaryIO, str, **str) -> None
    head_top = [
        'ID',
        'Frame Name',
        'Cycle Time [ms]',
        'Launch Type',
        'Launch Parameter',
        'Signal Byte No.',
        'Signal Bit No.',
        'Signal Name',
        'Signal Function',
        'Signal Length [Bit]',
        'Signal Default',
        ' Signal Not Available',
        'Byteorder',
        'is signed']
    head_tail = ['Name / Phys. Range', 'Function / Increment Unit', 'Value']

    additional_signal_columns = options.get("additionalAttributes", "").split(",")
    additional_frame_columns = options.get("additionalFrameAttributes", "").split(",")
    motorola_bit_format = options.get("xlsMotorolaBitFormat", "msbreverse")

    csv_table = list()  # List holding all csv rows

    col = 0  # Column counter

    # -- headers start:
    header_row = CsvRow()

    # write first row (header) cols before ECUs:
    for head in head_top:
        header_row.write(col, head)
        col += 1

    # write ECU in first row:
    ecu_name_list = []
    for ecu in db.ecus:
        header_row.write(col, ecu.name)
        ecu_name_list.append(ecu.name)
        col += 1

    # write first row (header) cols after ECUs:
    for head in head_tail:
        header_row.write(col, head)
        col += 1

    for additionalCol in additional_frame_columns:
        header_row.write(col, "frame." + additionalCol)
        col += 1

    for additionalCol in additional_signal_columns:
        header_row.write(col, "signal." + additionalCol)
        col += 1

    csv_table.append(header_row)
    # -- headers end...

    frame_hash = {}
    for frame in db.frames:
        if frame.is_complex_multiplexed:
            logger.error("export complex multiplexers is not supported - ignoring frame " + frame.name)
            continue
        frame_hash[int(frame.arbitration_id.id)] = frame

    # set row to first Frame (row = 0 is header)
    row = 1

    # iterate over the frames
    for idx in sorted(frame_hash.keys()):
        frame = frame_hash[idx]

        # sort signals:
        signal_hash = {}
        for sig in frame.signals:
            signal_hash["%02d" % int(sig.get_startbit()) + sig.name] = sig

        additional_frame_info = [
            frame.attribute(frameInfo, default="")
            for frameInfo in additional_frame_columns
        ]

        # iterate over signals
        for sig_idx in sorted(signal_hash.keys()):
            sig = signal_hash[sig_idx]

            # value table available?
            if sig.values.__len__() > 0:
                # iterate over values in value table
                for val in sorted(sig.values.keys()):
                    signal_row = CsvRow()
                    signal_row += canmatrix.formats.xls_common.get_frame_info(db, frame)

                    (front, back) = canmatrix.formats.xls_common.get_signal(db, sig, motorola_bit_format)
                    signal_row += front
                    signal_row += ("s" if sig.is_signed else "u")

                    col = head_top.__len__()
                    write_ecu_matrix(ecu_name_list, sig, frame, signal_row, col)
                    signal_row += back
                    # write Value
                    signal_row += [val, sig.values[val]]

                    signal_row += additional_frame_info
                    for item in additional_signal_columns:
                        temp = getattr(sig, item, "")
                        signal_row += [temp]

                    # next row
                    row += 1
                    csv_table.append(signal_row)
                # loop over values ends here
            # no value table available
            else:
                signal_row = CsvRow()
                signal_row += canmatrix.formats.xls_common.get_frame_info(db, frame)

                (front, back) = canmatrix.formats.xls_common.get_signal(db, sig, motorola_bit_format)
                signal_row += front
                signal_row += ("s" if sig.is_signed else "u")

                col = head_top.__len__()
                write_ecu_matrix(ecu_name_list, sig, frame, signal_row, col)
                signal_row += back

                if sig.min is not None or sig.max is not None:
                    signal_row += [str("{}..{}".format(sig.min, sig.max))]
                else:
                    signal_row += [""]

                signal_row += additional_frame_info
                for item in additional_signal_columns:
                    temp = getattr(sig, item, "")
                    signal_row += [temp]

                # next row
                row += 1
                csv_table.append(signal_row)
                # set style to normal - without border
        # loop over signals ends here
    # loop over frames ends here

    if sys.version_info > (3, 0):
        import io
        temp = io.TextIOWrapper(file_object, encoding='UTF-8')
    else:
        temp = file_object

    try:
        writer = csv.writer(temp, delimiter=delimiter)
        for csv_row in csv_table:
            writer.writerow(csv_row.as_list)
        # else:
        #    # just print to stdout
        #    finalTableString = "\n".join(
        #        [row.toCSV(delimiter) for row in csv_table])
        #    print(finalTableString)
    finally:
        if sys.version_info > (3, 0):
            # When TextIOWrapper is garbage collected, it closes the raw stream
            # unless the raw stream is detached first
            temp.detach()
