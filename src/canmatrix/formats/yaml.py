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
# this script imports and exports structured yaml files for a canmatrix object.
# the yaml structure mirrors the json format (see canmatrix.formats._dict_codec),
# so json and yaml describe the same logical model.

import typing

import canmatrix
from canmatrix.formats import _dict_codec

import yaml  # noqa: F401  (import guarded by formats/__init__.py)


def dump(db, f, **options):
    # type: (canmatrix.CanMatrix, typing.BinaryIO, **typing.Any) -> None
    export_dict = _dict_codec.to_dict(
        db,
        export_all=options.get('yamlExportAll', False),
        native_types=options.get('yamlNativeTypes', True),
        motorola_bit_format=options.get('yamlMotorolaBitFormat', "lsb"),
        additional_frame_columns=[x for x in options.get("additionalFrameAttributes", "").split(",") if x],
        frame_id_as_hex=options.get('yamlFrameIdAsHex', False),
    )
    text = yaml.safe_dump(export_dict, default_flow_style=False, sort_keys=True, allow_unicode=True)
    f.write(text.encode('utf-8'))


def load(f, **options):
    # type: (typing.BinaryIO, **typing.Any) -> canmatrix.CanMatrix
    yaml_data = yaml.safe_load(f)
    db = _dict_codec.from_dict(yaml_data, **options)
    f.close()
    return db
