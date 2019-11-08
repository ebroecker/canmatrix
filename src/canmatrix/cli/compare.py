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
import typing
from builtins import *

import click

import canmatrix.compare

logger = logging.getLogger(__name__)


@click.command()
@click.option('-v', '--verbose', 'verbosity', help="Output verbosity", count=True, default=1)
@click.option('-s', '--silent', is_flag=True, default=False, help="don't print status messages to stdout. (only errors)")
@click.option('-f', '--frames', is_flag=True, default=False, help="show list of frames")
@click.option('-c', '--comments', 'check_comments', is_flag=True, default=False, help="look for changed comments")
@click.option('-a', '--attributes', 'check_attributes', is_flag=True, default=False, help="look for changed attributes")
@click.option('-t', '--valueTable', 'ignore_valuetables', is_flag=True, default=False, help="ignore changed valuetables")
@click.argument('matrix1', required=True)
@click.argument('matrix2', required=True)
def cli_compare(matrix1, matrix2, verbosity, silent, check_comments, check_attributes, ignore_valuetables, frames):
    """
        canmatrix.cli.compare [options] matrix1 matrix2

        matrixX can be any of *.dbc|*.dbf|*.kcd|*.arxml|*.xls(x)|*.sym
    """

    import canmatrix.log
    root_logger = canmatrix.log.setup_logger()

    if silent:
        # Only print ERROR messages (ignore import warnings)
        verbosity = -1
    canmatrix.log.set_log_level(root_logger, verbosity)

    # import only after setting log level, to also disable warning messages in silent mode.
    import canmatrix.formats  # due this import we need the import alias for log module

    logger.info("Importing " + matrix1 + " ... ")
    db1 = canmatrix.formats.loadp_flat(matrix1)
    logger.info("%d Frames found" % (db1.frames.__len__()))

    logger.info("Importing " + matrix2 + " ... ")
    db2 = canmatrix.formats.loadp_flat(matrix2)
    logger.info("%d Frames found" % (db2.frames.__len__()))

    ignore = {}  # type: typing.Dict[str, typing.Union[str, bool]]

    if not check_comments:
        ignore["comment"] = "*"

    if not check_attributes:
        ignore["ATTRIBUTE"] = "*"

    if ignore_valuetables:
        ignore["VALUETABLES"] = True

    if frames:
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
    sys.exit(cli_compare())
