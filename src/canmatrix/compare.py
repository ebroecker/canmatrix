#!/usr/bin/env python3

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

from __future__ import print_function
from __future__ import absolute_import
import logging

from .log import setup_logger, set_log_level
import sys

logger = logging.getLogger(__name__)


class compareResult(object):

    def __init__(self, result=None, mtype=None, ref=None, changes=None):
        # equal, added, deleted, changed
        self._result = result
        # db, bu, frame, signal, attribute
        self._type = mtype
        # reference to related object
        self._ref = ref
        self._changes = changes
        self._children = []

    def addChild(self, child):
        self._children.append(child)


def propagateChanges(res):
    change = 0
    for child in res._children:
        change += propagateChanges(child)
    if change != 0:
        res._result = "changed"
    if res._result != "equal":
        return 1
    else:
        return 0


def compareDb(db1, db2, ignore=None):
    result = compareResult()
    for f1 in db1.frames:
        f2 = db2.frame_by_id(f1.id)
        if f2 is None:
            result.addChild(compareResult("deleted", "FRAME", f1))
        else:
            result.addChild(compareFrame(f1, f2, ignore))
    for f2 in db2.frames:
        f1 = db1.frame_by_id(f2.id)
        if f1 is None:
            result.addChild(compareResult("added", "FRAME", f2))

    if ignore is not None and "ATTRIBUTE" in ignore and ignore[
            "ATTRIBUTE"] == "*":
        pass
    else:
        result.addChild(compareAttributes(db1, db2, ignore))

    for bu1 in db1.boardUnits:
        bu2 = db2.ecu_by_name(bu1.name)
        if bu2 is None:
            result.addChild(compareResult("deleted", "ecu", bu1))
        else:
            result.addChild(compareBu(bu1, bu2, ignore))
    for bu2 in db2.boardUnits:
        bu1 = db1.ecu_by_name(bu2.name)
        if bu1 is None:
            result.addChild(compareResult("added", "ecu", bu2))

    if ignore is not None and "DEFINE" in ignore and ignore["DEFINE"] == "*":
        pass
    else:
        result.addChild(
            compareDefineList(
                db1.globalDefines,
                db2.globalDefines))

        temp = compareDefineList(db1.buDefines, db2.buDefines)
        temp._type = "ECU Defines"
        result.addChild(temp)

        temp = compareDefineList(db1.frameDefines, db2.frameDefines)
        temp._type = "Frame Defines"
        result.addChild(temp)

        temp = compareDefineList(db1.signalDefines, db2.signalDefines)
        temp._type = "Signal Defines"
        result.addChild(temp)

    if "VALUETABLES" in ignore and ignore["VALUETABLES"]:
        pass
    else:
        for vt1 in db1.valueTables:
            if vt1 not in db2.valueTables:
                result.addChild(
                    compareResult(
                        "deleted",
                        "valuetable " + vt1,
                        db1.valueTables))
            else:
                result.addChild(
                    compareValueTable(
                        db1.valueTables[vt1],
                        db2.valueTables[vt1]))

        for vt2 in db2.valueTables:
            if vt2 not in db1.valueTables:
                result.addChild(
                    compareResult(
                        "added",
                        "valuetable " + vt2,
                        db2.valueTables))

    propagateChanges(result)

    return result


def compareValueTable(vt1, vt2):
    result = compareResult("equal", "Valuetable", vt1)
    for value in vt1:
        if value not in vt2:
            result.addChild(
                compareResult(
                    "removed",
                    "Value " +
                    str(value),
                    vt1[value]))
        elif vt1[value] != vt2[value]:
            result.addChild(compareResult("changed", "Value " +
                                          str(value) +
                                          " " +
                                          str(vt1[value].encode('ascii', 'ignore')), [vt1[value], vt2[value]]))
    for value in vt2:
        if value not in vt1:
            result.addChild(
                compareResult(
                    "added",
                    "Value " +
                    str(value),
                    vt2[value]))
    return result


def compareSignalGroup(sg1, sg2):
    result = compareResult("equal", "SignalGroup", sg1)

    if sg1.name != sg2.name:
        result.addChild(
            compareResult(
                "changed", "SignalName", [
                    sg1.name, sg2.name]))
    if sg1.id != sg2.id:
        result.addChild(compareResult(
            "changed", "SignalName", [str(sg1.id), str(sg2.id)]))

    if sg1.signals is None or sg2.signals is None:
        logger.debug("Strange - sg wo members???")
        return result
    for member in sg1.signals:
        if sg2.by_name(member.name) is None:
            result.addChild(compareResult("deleted", str(member.name), member))
    for member in sg2.signals:
        if sg1.by_name(member.name) is None:
            result.addChild(compareResult("added", str(member.name), member))
    return result


def compareDefineList(d1list, d2list):
    result = compareResult("equal", "DefineList", d1list)
    for definition in d1list:
        if definition not in d2list:
            result.addChild(
                compareResult(
                    "deleted",
                    "Define" +
                    str(definition),
                    d1list))
        else:
            d2 = d2list[definition]
            d1 = d1list[definition]
            if d1.definition != d2.definition:
                result.addChild(
                    compareResult(
                        "changed", "Definition", d1.definition, [
                            d1.definition, d2.definition]))

            if d1.defaultValue != d2.defaultValue:
                result.addChild(
                    compareResult(
                        "changed", "DefaultValue", d1.definition, [
                            d1.defaultValue, d2.defaultValue]))
    for definition in d2list:
        if definition not in d1list:
            result.addChild(
                compareResult(
                    "added",
                    "Define" +
                    str(definition),
                    d2list))
    return result


def compareAttributes(ele1, ele2, ignore=None):
    result = compareResult("equal", "ATTRIBUTES", ele1)
    if ignore is not None and "ATTRIBUTE" in ignore and (
            ignore["ATTRIBUTE"] == "*" or ignore["ATTRIBUTE"] == ele1):
        return result
    for attribute in ele1.attributes:
        if attribute not in ele2.attributes:
            result.addChild(
                compareResult(
                    "deleted",
                    str(attribute),
                    ele1.attributes[attribute]))
        elif ele1.attributes[attribute] != ele2.attributes[attribute]:
            result.addChild(
                compareResult(
                    "changed", str(attribute), ele1.attributes[attribute], [
                        ele1.attributes[attribute], ele2.attributes[attribute]]))

    for attribute in ele2.attributes:
        if attribute not in ele1.attributes:
            result.addChild(
                compareResult(
                    "added",
                    str(attribute),
                    ele2.attributes[attribute]))
    return result


def compareBu(bu1, bu2, ignore=None):
    result = compareResult("equal", "ECU", bu1)

    if not "comment" in ignore:
        if bu1.comment != bu2.comment:
            result.addChild(
                compareResult(
                    "changed", "ECU", bu1, [
                        bu1.comment, bu2.comment]))

    if ignore is not None and "ATTRIBUTE" in ignore and ignore[
            "ATTRIBUTE"] == "*":
        pass
    else:
        result.addChild(compareAttributes(bu1, bu2, ignore))
    return result


def compareFrame(f1, f2, ignore=None):
    result = compareResult("equal", "FRAME", f1)

    for s1 in f1:
        s2 = f2.signal_by_name(s1.name)
        if not s2:
            result.addChild(compareResult("deleted", "SIGNAL", s1))
        else:
            result.addChild(compareSignal(s1, s2, ignore))

    if f1.name != f2.name:
        result.addChild(
            compareResult(
                "changed", "Name", f1, [
                    f1.name, f2.name]))
    if f1.size != f2.size:
        result.addChild(
            compareResult(
                "changed", "dlc", f1, [
                    "dlc: %d" %
                    f1.size, "dlc: %d" %
                    f2.size]))
    if f1.extended != f2.extended:
        result.addChild(
            compareResult(
                "changed", "FRAME", f1, [
                    "extended-Flag: %d" %
                    f1.extended, "extended-Flag: %d" %
                    f2.extended]))
    if not "comment" in ignore:
        if f2.comment is None:
            f2.add_comment("")
        if f1.comment is None:
            f1.add_comment("")
        if f1.comment != f2.comment:
            result.addChild(
                compareResult(
                    "changed", "FRAME", f1, [
                        "comment: " + f1.comment, "comment: " + f2.comment]))

    for s2 in f2.signals:
        s1 = f1.signal_by_name(s2.name)
        if not s1:
            result.addChild(compareResult("added", "SIGNAL", s2))

    if ignore is not None and "ATTRIBUTE" in ignore and ignore[
            "ATTRIBUTE"] == "*":
        pass
    else:
        result.addChild(compareAttributes(f1, f2, ignore))

    temp = [str(item) for item in f2.transmitters]
    for transmitter in f1.transmitters:
        if transmitter not in temp:
            result.addChild(compareResult("removed", "Frame-Transmitter", f1))

    temp = [str(item) for item in f1.transmitters]
    for transmitter in f2.transmitters:
        if transmitter not in temp:
            result.addChild(compareResult("added", "Frame-Transmitter",  f2))

    for sg1 in f1.signalGroups:
        sg2 = f2.signal_group_by_name(sg1.name)
        if sg2 is None:
            result.addChild(compareResult("removed", "Signalgroup", sg1))
        else:
            result.addChild(compareSignalGroup(sg1, sg2))

    for sg2 in f2.signalGroups:
        if f1.signal_group_by_name(sg2.name) is None:
            result.addChild(compareResult("added", "Signalgroup", sg2))
    return result


def compareSignal(s1, s2, ignore=None):
    result = compareResult("equal", "SIGNAL", s1)

    if s1.startBit != s2.startBit:
        result.addChild(
            compareResult(
                "changed", "startbit", s1, [
                    " %d" %
                    s1.startBit, " %d" %
                    s2.startBit]))
    if s1.size != s2.size:
        result.addChild(
            compareResult(
                "changed", "signalsize", s1, [
                    " %d" %
                    s1.size, " %d" %
                    s2.size]))
    if float(s1.factor) != float(s2.factor):
        result.addChild(
            compareResult(
                "changed", "factor", s1, [
                    s1.factor, s2.factor]))
    if float(s1.offset) != float(s2.offset):
        result.addChild(
            compareResult(
                "changed", "offset", s1, [
                    s1.offset, s2.offset]))
    if float(s1.min) != float(s2.min):
        result.addChild(
            compareResult(
                "changed", "min", s1, [
                    s1.min, s2.min]))
    if float(s1.max) != float(s2.max):
        result.addChild(
            compareResult(
                "changed", "max", s1, [
                    s1.max, s2.max]))
    if s1.is_little_endian != s2.is_little_endian:
        result.addChild(
            compareResult(
                "changed", "is_little_endian", s1, [
                    " %d" %
                    s1.is_little_endian, " %d" %
                    s2.is_little_endian]))
    if s1.is_signed != s2.is_signed:
        result.addChild(
            compareResult(
                "changed", "sign", s1, [
                    " %d" %
                    s1.is_signed, " %d" %
                    s2.is_signed]))
    if s1.multiplex != s2.multiplex:
        result.addChild(compareResult("changed", "multiplex", s1, [
                        str(s1.multiplex), str(s2.multiplex)]))
    if s1.unit != s2.unit:
        result.addChild(
            compareResult(
                "changed", "unit", s1, [
                    s1.unit, s2.unit]))
    if not "comment" in ignore:
        if s1.comment is not None and s2.comment is not None and s1.comment != s2.comment:
            if s1.comment.replace("\n", " ") != s2.comment.replace("\n", " "):
                result.addChild(
                    compareResult(
                        "changed", "comment", s1, [
                            s1.comment, s2.comment]))
            else:
                result.addChild(
                    compareResult(
                        "changed", "comment", s1, [
                            "only whitespaces differ", ""]))

    for receiver in s1.receiver:
        if receiver.strip() not in s2.receiver:
            result.addChild(
                compareResult(
                    "removed",
                    "receiver " +
                    receiver,
                    s1.receiver))

    for receiver in s2.receiver:
        if receiver.strip() not in s1.receiver:
            result.addChild(
                compareResult(
                    "added",
                    "receiver " +
                    receiver,
                    s1.receiver))

    if ignore is not None and "ATTRIBUTE" in ignore and ignore[
            "ATTRIBUTE"] == "*":
        pass
    else:
        result.addChild(compareAttributes(s1, s2, ignore))

    if "VALUETABLES" in ignore and ignore["VALUETABLES"]:
        pass
    else:
        result.addChild(compareValueTable(s1.values, s2.values))

    return result


def dumpResult(res, depth=0):
    if res._type is not None and res._result != "equal":
        for _ in range(0, depth):
            print(" ", end=' ')
        print(res._type + " " + res._result + " ", end=' ')
        if hasattr(res._ref, 'name'):
            print(res._ref.name)
        else:
            print(" ")
        if res._changes is not None and res._changes[
                0] is not None and res._changes[1] is not None:
            for _ in range(0, depth):
                print(" ", end=' ')
            print (type(res._changes[0]))
            if sys.version_info[0] < 3:
                if isinstance(res._changes[0], type(u'')):
                    res._changes[0] = res._changes[0].encode('ascii', 'ignore')
                if isinstance(res._changes[1], type(u'')):
                    res._changes[1] = res._changes[1].encode('ascii', 'ignore')
            else:
                if type(res._changes[0]) == str:
                    res._changes[0] = res._changes[0].encode('ascii', 'ignore')
                if type(res._changes[1]) == str:
                    res._changes[1] = res._changes[1].encode('ascii', 'ignore')
            print("old: " +
                  str(res._changes[0]) +
                  " new: " +
                  str(res._changes[1]))
    for child in res._children:
        dumpResult(child, depth + 1)


def main():
    setup_logger()
    from optparse import OptionParser

    usage = """
    %prog [options] cancompare matrix1 matrix2

    matrixX can be any of *.dbc|*.dbf|*.kcd|*.arxml
    """

    parser = OptionParser(usage=usage)
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
        "-f","--frames",
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
    set_log_level(logger, verbosity)

    # import only after setting log level, to also disable warning messages in
    # silent mode.
    import canmatrix.formats

    logger.info("Importing " + matrix1 + " ... ")
    db1 = next(iter(canmatrix.formats.loadp(matrix1).values()))
    logger.info("%d Frames found" % (db1.frames.__len__()))

    logger.info("Importing " + matrix2 + " ... ")
    db2 = next(iter(canmatrix.formats.loadp(matrix2).values()))
    logger.info("%d Frames found" % (db2.frames.__len__()))

    ignore = {}

    if not cmdlineOptions.check_comments:
        ignore["comment"] = "*"

    if not cmdlineOptions.check_attributes:
        ignore["ATTRIBUTE"] = "*"


    if cmdlineOptions.ignore_valuetables:
        ignore["VALUETABLES"] = True

    if cmdlineOptions.frames:
        onlyInMatrix1 = []
        onlyInMatrix2 = []
        for frame in db1.frames:
            if db2.frame_by_name(frame.name) is None:
                onlyInMatrix1.append(frame.name)
        for frame in db2.frames:
            if db1.frame_by_name(frame.name) is None:
                onlyInMatrix2.append(frame.name)
        print ("Frames only in " + matrix1 + ": " + " ".join(onlyInMatrix1))
        print ("Frames only in " + matrix2 + ": " + " ".join(onlyInMatrix2))

    else:
        #ignore["ATTRIBUTE"] = "*"
        #ignore["DEFINE"] = "*"
        obj = compareDb(db1, db2, ignore)
        dumpResult(obj)

if __name__ == '__main__':
    sys.exit(main())
