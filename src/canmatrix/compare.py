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

import canmatrix

logger = logging.getLogger(__name__)
ConfigDict = typing.Optional[typing.Mapping[str, typing.Union[str, bool]]]
WithAttribute = typing.TypeVar("WithAttribute", canmatrix.CanMatrix, canmatrix.Ecu, canmatrix.Frame, canmatrix.Signal)


@attr.s
class CompareResult(object):
    """Hold comparison results in logical tree."""
    result = attr.ib(default=None)  # type: typing.Optional[str]    # any of equal, added, deleted, changed
    type = attr.ib(default=None)  # type: typing.Optional[str]      # db, ecu, frame, signal, signalGroup or attribute
    ref = attr.ib(default=None)  # type: typing.Any                 # reference to related object
    changes = attr.ib(default=None)  # type: typing.Optional[typing.List]
    _children = attr.ib(factory=list)  # type: typing.List[CompareResult]  # nested CompareResults

    def add_child(self, child):
        # type: (CompareResult) -> None
        self._children.append(child)

    @property
    def children(self):  # type: () -> typing.List[CompareResult]
        return self._children


def propagate_changes(res):  # type: (CompareResult) -> int
    change = 0
    for child in res.children:
        change += propagate_changes(child)
    if change != 0:
        res.result = "changed"
    if res.result != "equal":
        return 1
    else:
        return 0


def compare_db(db1, db2, ignore=None):
    # type: (canmatrix.CanMatrix, canmatrix.CanMatrix, ConfigDict) -> CompareResult
    result = CompareResult()
    if ignore is None:
        ignore = dict()
    for f1 in db1.frames:
        f2 = db2.frame_by_id(f1.arbitration_id)
        if f2 is None:
            result.add_child(CompareResult("deleted", "FRAME", f1))
        else:
            result.add_child(compare_frame(f1, f2, ignore))
    for f2 in db2.frames:
        f1 = db1.frame_by_id(f2.arbitration_id)
        if f1 is None:
            result.add_child(CompareResult("added", "FRAME", f2))

    if "ATTRIBUTE" in ignore and ignore["ATTRIBUTE"] == "*":
        pass
    else:
        result.add_child(compare_attributes(db1, db2, ignore))

    for ecu1 in db1.ecus:
        ecu2 = db2.ecu_by_name(ecu1.name)
        if ecu2 is None:
            result.add_child(CompareResult("deleted", "ecu", ecu1))
        else:
            result.add_child(compare_ecu(ecu1, ecu2, ignore))
    for ecu2 in db2.ecus:
        ecu1 = db1.ecu_by_name(ecu2.name)
        if ecu1 is None:
            result.add_child(CompareResult("added", "ecu", ecu2))

    if "DEFINE" in ignore and ignore["DEFINE"] == "*":
        pass
    else:
        result.add_child(
            compare_define_list(
                db1.global_defines,
                db2.global_defines))

        temp = compare_define_list(db1.ecu_defines, db2.ecu_defines)
        temp.type = "ECU Defines"
        result.add_child(temp)

        temp = compare_define_list(db1.frame_defines, db2.frame_defines)
        temp.type = "Frame Defines"
        result.add_child(temp)

        temp = compare_define_list(db1.signal_defines, db2.signal_defines)
        temp.type = "Signal Defines"
        result.add_child(temp)

    if "VALUETABLES" in ignore and ignore["VALUETABLES"]:
        pass
    else:
        for vt1 in db1.value_tables:
            if vt1 not in db2.value_tables:
                result.add_child(
                    CompareResult(
                        "deleted",
                        "valuetable " + vt1,
                        db1.value_tables))
            else:
                result.add_child(
                    compare_value_table(
                        db1.value_tables[vt1],
                        db2.value_tables[vt1]))

        for vt2 in db2.value_tables:
            if vt2 not in db1.value_tables:
                result.add_child(
                    CompareResult(
                        "added",
                        "valuetable " + vt2,
                        db2.value_tables))

    propagate_changes(result)

    return result


def compare_value_table(vt1, vt2):
    # type: (typing.Mapping, typing.Mapping) -> CompareResult
    result = CompareResult("equal", "Valuetable", vt1)
    for value in vt1:
        if value not in vt2:
            result.add_child(
                CompareResult(
                    "removed",
                    "Value " +
                    str(value),
                    vt1[value]))
        elif vt1[value] != vt2[value]:
            result.add_child(CompareResult("changed", "Value " +
                                           str(value) +
                                           " " +
                                           str(vt1[value].encode('ascii', 'ignore')), [vt1[value], vt2[value]]))
    for value in vt2:
        if value not in vt1:
            result.add_child(
                CompareResult(
                    "added",
                    "Value " +
                    str(value),
                    vt2[value]))
    return result


def compare_signal_group(sg1, sg2):
    # type: (canmatrix.SignalGroup, canmatrix.SignalGroup) -> CompareResult
    result = CompareResult("equal", "SignalGroup", sg1)

    if sg1.name != sg2.name:
        result.add_child(
            CompareResult(
                "changed", "SignalName", [
                    sg1.name, sg2.name]))
    if sg1.id != sg2.id:
        result.add_child(CompareResult(
            "changed", "SignalName", [str(sg1.id), str(sg2.id)]))

    if sg1.signals is None or sg2.signals is None:
        logger.debug("Strange - sg wo members???")
        return result
    for signal in sg1.signals:
        if sg2.by_name(signal.name) is None:
            result.add_child(CompareResult("deleted", str(signal.name), signal))
    for signal in sg2.signals:
        if sg1.by_name(signal.name) is None:
            result.add_child(CompareResult("added", str(signal.name), signal))
    return result


def compare_define_list(d1list, d2list):
    # type: (typing.Mapping[str, canmatrix.Define], typing.Mapping[str, canmatrix.Define]) -> CompareResult
    result = CompareResult("equal", "DefineList", d1list)
    for definition in d1list:
        if definition not in d2list:
            result.add_child(
                CompareResult(
                    "deleted",
                    "Define" +
                    str(definition),
                    d1list))
        else:
            d2 = d2list[definition]
            d1 = d1list[definition]
            if d1.definition != d2.definition:
                result.add_child(
                    CompareResult(
                        "changed", "Definition", d1.definition, [
                            d1.definition, d2.definition]))

            if d1.defaultValue != d2.defaultValue:
                result.add_child(
                    CompareResult(
                        "changed", "DefaultValue", d1.definition, [
                            d1.defaultValue, d2.defaultValue]))
    for definition in d2list:
        if definition not in d1list:
            result.add_child(
                CompareResult(
                    "added",
                    "Define" +
                    str(definition),
                    d2list))
    return result


def compare_attributes(ele1, ele2, ignore=None):
    # type: (WithAttribute, WithAttribute, ConfigDict) -> CompareResult
    if ignore is None:
        ignore = dict()
    result = CompareResult("equal", "ATTRIBUTES", ele1)
    if "ATTRIBUTE" in ignore and (
            ignore["ATTRIBUTE"] == "*" or ignore["ATTRIBUTE"] == ele1):
        return result
    for attribute in ele1.attributes:
        if attribute not in ele2.attributes:
            result.add_child(
                CompareResult(
                    "deleted",
                    str(attribute),
                    ele1.attributes[attribute]))
        elif ele1.attributes[attribute] != ele2.attributes[attribute]:
            result.add_child(
                CompareResult(
                    "changed", str(attribute), ele1.attributes[attribute], [
                        ele1.attributes[attribute], ele2.attributes[attribute]]))

    for attribute in ele2.attributes:
        if attribute not in ele1.attributes:
            result.add_child(
                CompareResult(
                    "added",
                    str(attribute),
                    ele2.attributes[attribute]))
    return result


def compare_ecu(ecu1, ecu2, ignore=None):
    # type: (canmatrix.Ecu, canmatrix.Ecu, ConfigDict) -> CompareResult
    if ignore is None:
        ignore = dict()
    result = CompareResult("equal", "ECU", ecu1)

    if "comment" not in ignore:
        if ecu1.comment != ecu2.comment:
            result.add_child(
                CompareResult(
                    "changed", "ECU", ecu1, [
                        ecu1.comment, ecu2.comment]))

    if "ATTRIBUTE" in ignore and ignore["ATTRIBUTE"] == "*":
        pass
    else:
        result.add_child(compare_attributes(ecu1, ecu2, ignore))
    return result


def compare_frame(f1, f2, ignore=None):
    # type: (canmatrix.Frame, canmatrix.Frame, ConfigDict) -> CompareResult
    if ignore is None:
        ignore = dict()
    result = CompareResult("equal", "FRAME", f1)

    for s1 in f1:
        s2 = f2.signal_by_name(s1.name)
        if not s2:
            result.add_child(CompareResult("deleted", "SIGNAL", s1))
        else:
            result.add_child(compare_signal(s1, s2, ignore))

    if f1.name != f2.name:
        result.add_child(
            CompareResult(
                "changed", "Name", f1, [
                    f1.name, f2.name]))
    if f1.size != f2.size:
        result.add_child(
            CompareResult(
                "changed", "dlc", f1, [
                    "dlc: %d" %
                    f1.size, "dlc: %d" %
                    f2.size]))
    if f1.arbitration_id.extended != f2.arbitration_id.extended:
        result.add_child(
            CompareResult(
                "changed", "FRAME", f1, [
                    "extended-Flag: %d" %
                    f1.arbitration_id.extended, "extended-Flag: %d" %
                    f2.arbitration_id.extended]))
    if "comment" not in ignore:
        if f2.comment is None:
            f2.add_comment("")
        if f1.comment is None:
            f1.add_comment("")
        if f1.comment != f2.comment:
            result.add_child(
                CompareResult(
                    "changed", "FRAME", f1, [
                        "comment: " + f1.comment, "comment: " + f2.comment]))

    for s2 in f2.signals:
        s1 = f1.signal_by_name(s2.name)
        if not s1:
            result.add_child(CompareResult("added", "SIGNAL", s2))

    if "ATTRIBUTE" in ignore and ignore["ATTRIBUTE"] == "*":
        pass
    else:
        result.add_child(compare_attributes(f1, f2, ignore))

    temp = [str(item) for item in f2.transmitters]
    for transmitter in f1.transmitters:
        if transmitter not in temp:
            result.add_child(CompareResult("removed", "Frame-Transmitter", f1))

    temp = [str(item) for item in f1.transmitters]
    for transmitter in f2.transmitters:
        if transmitter not in temp:
            result.add_child(CompareResult("added", "Frame-Transmitter", f2))

    for sg1 in f1.signalGroups:
        sg2 = f2.signal_group_by_name(sg1.name)
        if sg2 is None:
            result.add_child(CompareResult("removed", "Signalgroup", sg1))
        else:
            result.add_child(compare_signal_group(sg1, sg2))

    for sg2 in f2.signalGroups:
        if f1.signal_group_by_name(sg2.name) is None:
            result.add_child(CompareResult("added", "Signalgroup", sg2))
    return result


def compare_signal(s1, s2, ignore=None):
    # type: (canmatrix.Signal, canmatrix.Signal, ConfigDict) -> CompareResult
    if ignore is None:
        ignore = dict()
    result = CompareResult("equal", "SIGNAL", s1)

    if s1.start_bit != s2.start_bit:
        result.add_child(
            CompareResult(
                "changed", "startbit", s1, [
                    " %d" %
                    s1.start_bit, " %d" %
                    s2.start_bit]))
    if s1.size != s2.size:
        result.add_child(
            CompareResult(
                "changed", "signalsize", s1, [
                    " %d" %
                    s1.size, " %d" %
                    s2.size]))
    if float(s1.factor) != float(s2.factor):
        result.add_child(
            CompareResult(
                "changed", "factor", s1, [
                    s1.factor, s2.factor]))
    if float(s1.offset) != float(s2.offset):
        result.add_child(
            CompareResult(
                "changed", "offset", s1, [
                    s1.offset, s2.offset]))
    if float(s1.min) != float(s2.min):
        result.add_child(
            CompareResult(
                "changed", "min", s1, [
                    s1.min, s2.min]))
    if float(s1.max) != float(s2.max):
        result.add_child(
            CompareResult(
                "changed", "max", s1, [
                    s1.max, s2.max]))
    if s1.is_little_endian != s2.is_little_endian:
        result.add_child(
            CompareResult(
                "changed", "is_little_endian", s1, [
                    " %d" %
                    s1.is_little_endian, " %d" %
                    s2.is_little_endian]))
    if s1.is_signed != s2.is_signed:
        result.add_child(
            CompareResult(
                "changed", "sign", s1, [
                    " %d" %
                    s1.is_signed, " %d" %
                    s2.is_signed]))
    if s1.multiplex != s2.multiplex:
        result.add_child(CompareResult("changed", "multiplex", s1, [
            str(s1.multiplex), str(s2.multiplex)]))
    if s1.unit != s2.unit:
        result.add_child(
            CompareResult(
                "changed", "unit", s1, [
                    s1.unit, s2.unit]))
    if "comment" not in ignore:
        if s1.comment is not None and s2.comment is not None and s1.comment != s2.comment:
            if s1.comment.replace("\n", " ") != s2.comment.replace("\n", " "):
                result.add_child(
                    CompareResult(
                        "changed", "comment", s1, [
                            s1.comment, s2.comment]))
            else:
                result.add_child(
                    CompareResult(
                        "changed", "comment", s1, [
                            "only whitespaces differ", ""]))

    for receiver in s1.receivers:
        if receiver.strip() not in s2.receivers:
            result.add_child(
                CompareResult(
                    "removed",
                    "receiver " +
                    receiver,
                    s1.receivers))

    for receiver in s2.receivers:
        if receiver.strip() not in s1.receivers:
            result.add_child(
                CompareResult(
                    "added",
                    "receiver " +
                    receiver,
                    s1.receivers))

    if "ATTRIBUTE" in ignore and ignore["ATTRIBUTE"] == "*":
        pass
    else:
        result.add_child(compare_attributes(s1, s2, ignore))

    if "VALUETABLES" in ignore and ignore["VALUETABLES"]:
        pass
    else:
        result.add_child(compare_value_table(s1.values, s2.values))

    return result


def dump_result(res, depth=0):
    # type: (CompareResult, int) -> None
    if res.type is not None and res.result != "equal":
        for _ in range(0, depth):
            print(" ", end=' ')
        print(res.type + " " + res.result + " ", end=' ')
        if hasattr(res.ref, 'name'):
            print(res.ref.name)
        else:
            print(" ")
        if res.changes is not None and res.changes[0] is not None and res.changes[1] is not None:
            for _ in range(0, depth):
                print(" ", end=' ')
            print(type(res.changes[0]))
            if sys.version_info[0] < 3:
                if isinstance(res.changes[0], type(u'')):
                    res.changes[0] = res.changes[0].encode('ascii', 'ignore')
                if isinstance(res.changes[1], type(u'')):
                    res.changes[1] = res.changes[1].encode('ascii', 'ignore')
            else:
                if type(res.changes[0]) == str:
                    res.changes[0] = res.changes[0].encode('ascii', 'ignore')
                if type(res.changes[1]) == str:
                    res.changes[1] = res.changes[1].encode('ascii', 'ignore')
            print("old: " +
                  str(res.changes[0]) +
                  " new: " +
                  str(res.changes[1]))
    for child in res.children:
        dump_result(child, depth + 1)