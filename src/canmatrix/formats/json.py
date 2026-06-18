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

#
# this script exports json-files from a canmatrix-object
# json-files are the can-matrix-definitions of the CANard-project
# (https://github.com/ericevenchick/CANard)

import json
import typing
from builtins import *
import canmatrix

from canmatrix.formats import _dict_codec


def dump(db, f, **options):
    # type: (canmatrix.CanMatrix, typing.BinaryIO, **str) -> None

    export_dict = _dict_codec.to_dict(
        db,
        export_all=options.get('jsonExportAll', False),
        native_types=options.get('jsonNativeTypes', False),
        motorola_bit_format=options.get('jsonMotorolaBitFormat', "lsb"),
        export_canard=options.get('jsonExportCanard', False),
        additional_frame_columns=[x for x in options.get("additionalFrameAttributes", "").split(",") if x],
    )

    import io
    temp = io.TextIOWrapper(f, encoding='UTF-8')

    try:
        json.dump(export_dict, temp, sort_keys=True,
                  indent=4, separators=(',', ': '))
    finally:
        # When TextIOWrapper is garbage collected, it closes the raw stream
        # unless the raw stream is detached first
        temp.detach()


def load(f, **options):
    # type: (typing.BinaryIO, **str) -> canmatrix.CanMatrix
    import io
    json_data = json.load(io.TextIOWrapper(f, encoding='UTF-8'))
    db = _dict_codec.from_dict(json_data, **options)
    f.close()
    return db
