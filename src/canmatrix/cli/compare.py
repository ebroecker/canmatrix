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
import optparse
import sys
import typing

import attr
import canmatrix.compare

logger = logging.getLogger(__name__)


def main():  # type: () -> int
    import canmatrix.log
    canmatrix.log.setup_logger()

    usage = """
    %prog [options] cancompare matrix1 matrix2

    matrixX can be any of *.dbc|*.dbf|*.kcd|*.arxml
    """

    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-s",
        dest="silent",
        action="store_true",
        help="don't print status messages to stdout. (only errors)",
        default=False)
    parser.add_option(
        "-v",
        dest="verbosity",
        action="count",
        help="Output verbosity",
        default=0)
    parser.add_option(
        "-f", "--frames",
        dest="frames",
        action="store_true",
        help="show list of frames",
        default=False)
    parser.add_option(
        "-c", "--comments",
        dest="check_comments",
        action="store_true",
        help="check changed comments",
        default=False)
    parser.add_option(
        "-a", "--attributes",
        dest="check_attributes",
        action="store_true",
        help="check changed attributes",
        default=False)
    parser.add_option(
        "-t", "--valueTable",
        dest="ignore_valuetables",
        action="store_true",
        help="check changed valuetables",
        default=False)

    (cmdlineOptions, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    matrix1 = args[0]
    matrix2 = args[1]

    verbosity = cmdlineOptions.verbosity
    if cmdlineOptions.silent:
        # Only print ERROR messages (ignore import warnings)
        verbosity = -1
    canmatrix.log.set_log_level(logger, verbosity)

    # import only after setting log level, to also disable warning messages in silent mode.
    import canmatrix.formats  # due this import we need the import alias for log module

    logger.info("Importing " + matrix1 + " ... ")
    db1 = next(iter(canmatrix.formats.loadp(matrix1).values()))
    logger.info("%d Frames found" % (db1.frames.__len__()))

    logger.info("Importing " + matrix2 + " ... ")
    db2 = next(iter(canmatrix.formats.loadp(matrix2).values()))
    logger.info("%d Frames found" % (db2.frames.__len__()))

    ignore = {}  # type: typing.Dict[str, typing.Union[str, bool]]

    if not cmdlineOptions.check_comments:
        ignore["comment"] = "*"

    if not cmdlineOptions.check_attributes:
        ignore["ATTRIBUTE"] = "*"

    if cmdlineOptions.ignore_valuetables:
        ignore["VALUETABLES"] = True

    if cmdlineOptions.frames:
        only_in_matrix1 = [
            frame.name
            for frame in db1.frames
            if db2.frame_by_name(frame.name) is None
        ]
        only_in_matrix2 = [
            frame.name
            for frame in db2.frames
            if db1.frame_by_name(frame.name) is None
        ]
        print("Frames only in " + matrix1 + ": " + " ".join(only_in_matrix1))
        print("Frames only in " + matrix2 + ": " + " ".join(only_in_matrix2))

    else:
        # ignore["ATTRIBUTE"] = "*"
        # ignore["DEFINE"] = "*"
        obj = canmatrix.compare.compare_db(db1, db2, ignore)
        canmatrix.compare.dump_result(obj)
    return 0


# to be run as module `python -m canmatrix.compare`, NOT as script with argument `canmatrix/compare.py`
if __name__ == '__main__':
    sys.exit(main())
