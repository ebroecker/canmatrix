# -*- coding: utf-8 -*-
# Copyright (c) 2013, Eduard Broecker
# With contributions 2025, Gabriele Omodeo Vanone
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,   PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR  OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import typing
import attr

import canmatrix.utils
from decimal import Decimal as DefaultFloatFactory

class Define(object):
    """
    Hold the defines and default-values.
    """

    def __init__(self, definition):  # type (str) -> None
        """Initialize Define object.

        :param str definition: definition string. Ex: "INT -5 10"
        """
        definition = definition.strip()
        self.definition = definition
        self.type = None  # type: typing.Optional[str]
        self.defaultValue = None  # type: typing.Any

        def safe_convert_str_to_int(inStr):  # type: (str) -> int
            """Convert string to int safely. Check that it isn't float.

            :param str inStr: integer represented as string.
            :rtype: int
            """
            out = int(DefaultFloatFactory(inStr))
            if out != DefaultFloatFactory(inStr):
                logger.warning("Warning, integer was expected but got float: got: {0} using {1}\n".format(inStr, str(out)))
            return out

        # for any known type:
        if definition[0:3] == 'INT':
            self.type = 'INT'
            min, max = definition[4:].split(' ', 2)
            self.min = safe_convert_str_to_int(min)
            self.max = safe_convert_str_to_int(max)

        elif definition[0:6] == 'STRING':
            self.type = 'STRING'
            self.min = None
            self.max = None

        elif definition[0:4] == 'ENUM':
            self.type = 'ENUM'
            tempValues = canmatrix.utils.quote_aware_comma_split(definition[5:])
            self.values = []  # type: typing.List[str]
            for value in tempValues:
                value = value.replace("vector_leerstring", "")
                self.values.append(value)

        elif definition[0:3] == 'HEX':  # differently rendered in DBC editor, but values are saved like for an INT
            self.type = 'HEX'
            min, max = definition[4:].split(' ', 2)
            self.min = safe_convert_str_to_int(min)
            self.max = safe_convert_str_to_int(max)

        elif definition[0:5] == 'FLOAT':
            self.type = 'FLOAT'
            min, max = definition[6:].split(' ', 2)
            self.min = DefaultFloatFactory(min)
            self.max = DefaultFloatFactory(max)

    def set_default(self, default):  # type: (typing.Any) -> None
        """Set Definition default value.

        :param default: default value; number, str or quoted str ("value")
        """
        if default is not None and len(default) > 1 and default[0] == '"' and default[-1] == '"':
            default = default[1:-1]
        self.defaultValue = default

    def update(self):  # type: () -> None
        """Update definition string for type ENUM.

        For type ENUM rebuild the definition string from current values. Otherwise do nothing.
        """
        if self.type != 'ENUM':
            return
        self.definition = 'ENUM "' + '","' .join(self.values) +'"'
