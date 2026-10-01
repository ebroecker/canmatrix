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

import canmatrix.types
import canmatrix.exceptions
@attr.s
class Ecu(object):
    """
    Represents one ECU.
    """

    name = attr.ib()  # type: str
    comment = attr.ib(default=None)  # type: typing.Optional[str]
    attributes = attr.ib(factory=dict, repr=False)  # type: typing.MutableMapping[str, typing.Any]

    def attribute(self, attribute_name, db=None, default=None):  # type: (str, CanMatrix.CanMatrix, typing.Any) -> typing.Any
        """Get Board unit attribute by its name.

        :param str attribute_name: attribute name.
        :param CanMatrix db: Optional database parameter to get global default attribute value.
        :param default: Default value if attribute doesn't exist.
        :return: Return the attribute value if found, else `default` or None
        """
        if attribute_name in self.attributes:
            return self.attributes[attribute_name]
        elif db is not None:
            if attribute_name in db.ecu_defines:
                define = db.ecu_defines[attribute_name]
                return define.defaultValue
        return default

    def add_attribute(self, attribute, value):  # type (attribute: str, value: typing.Any) -> None
        """
        Add the Attribute to current ECU. If the attribute already exists, update the value.

        :param str attribute: Attribute name
        :param any value: Attribute value
        """
        try:
            self.attributes[attribute] = str(value)
        except UnicodeDecodeError:
            self.attributes[attribute] = value
        if type(self.attributes[attribute]) == str:
            self.attributes[attribute] = self.attributes[attribute].strip()

    def del_attribute(self, attribute):
        if attribute in self.attributes:
            del self.attributes[attribute]

    def add_comment(self, comment):  # type: (str) -> None
        """
        Set ECU comment.

        :param str comment: BU comment/description.
        """
        self.comment = comment
