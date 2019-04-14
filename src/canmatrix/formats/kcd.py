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
# this script exports kcd-files from a canmatrix-object
# kcd-files are the can-matrix-definitions of the kayak
# (http://kayak.2codeornot2code.org/)

from __future__ import absolute_import
from __future__ import division

import decimal
import os
import re
import typing
from builtins import *

from lxml import etree

import canmatrix
import canmatrix.cancluster

clusterExporter = 1
clusterImporter = 1

_Element = etree._Element


def default_float_factory(value):  # type: (typing.Any) -> decimal.Decimal
    return decimal.Decimal(value)


def create_signal(signal, node_list, type_enums):
    # type: (canmatrix.Signal, typing.Mapping[str, int], typing.Mapping[str, typing.Sequence[str]]) -> _Element
    xml_signal = etree.Element(
        'Signal',
        name=signal.name,
        offset=str(signal.get_startbit()))
    if signal.size > 1:
        xml_signal.set("length", str(signal.size))
    if not signal.is_little_endian:
        xml_signal.set('endianess', "big")

    comment = signal.comment if signal.comment else ""
    more_comments = ""
    for attrib, val in sorted(signal.attributes.items()):
        try:
            if attrib in type_enums and int(val) < len(type_enums[attrib]):
                val = type_enums[attrib][int(val)]
            more_comments += ("\n" + attrib + ': ' + val)
        except:
            pass
    if more_comments:
        comment += "\n" + more_comments

    if comment:
        notes = etree.Element('Notes')
        notes.text = comment
        xml_signal.append(notes)

    consumer = etree.Element('Consumer')
    for receiver in signal.receivers:
        if receiver in node_list and len(receiver) > 1:
            node_ref = etree.Element('NodeRef', id=str(node_list[receiver]))
            consumer.append(node_ref)
        if len(consumer) > 0:  # if consumer has children
            xml_signal.append(consumer)
    value = etree.Element('Value')
    if signal.is_float:
        if signal.size > 32:
            value.set('type', "double")
        else:
            value.set('type', "single")
    elif signal.is_signed:
        value.set('type', "signed")

    if float(signal.factor) != 1:
        value.set('slope', str("%g" % signal.factor))
    if float(signal.offset) != 0:
        value.set('intercept', str("%g" % signal.offset))
    if float(signal.min) != 0:
        value.set('min', str("{:.16g}".format(signal.min)))
    if float(signal.max) != 1 and float(signal.max) != 0:
        value.set('max', str("{:.16g}".format(signal.max)))
    if len(signal.unit) > 0:
        value.set('unit', signal.unit)

    if len(value.attrib) > 0:
        xml_signal.append(value)

    if signal.values:  # signal has value table
        label_set = etree.Element('LabelSet')
        for table_value, table_name in sorted(signal.values.items(), key=lambda x: int(x[0])):
            label = etree.Element(
                'Label',
                name=table_name.replace('"', ''),
                value=str(table_value))
            label_set.append(label)
        xml_signal.append(label_set)

    return xml_signal


def dump(dbs, f, **_options):
    # type: (canmatrix.cancluster.CanCluster, typing.IO, **typing.Any) -> None
    signal_type_enums = {}
    cluster = canmatrix.cancluster.CanCluster(dbs)
    for name in cluster:  # type: str
        db = cluster[name]
        for (typename, define) in list(db.signal_defines.items()):
            defines = re.split(r"\s+", define.definition)  # type: typing.Sequence[str]
            define_type = defines[0]
            if define_type != 'ENUM':
                continue
            enum_str = defines[1].strip('"')
            enum_literals = enum_str.split('","')
            signal_type_enums[typename] = enum_literals

    # create XML
    root = etree.Element('NetworkDefinition')  # type: _Element
    root.set("xmlns", "http://kayak.2codeornot2code.org/1.0")
    ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(ns_xsi + "schemaLocation", "Definition.xsd")

    # root.append(etree.Element('Document'))
    # another child with text

    child = etree.Element('Document')
    child.set("name", "Some Document Name")
    child.text = 'some text'
    root.append(child)

    # Nodes:
    element_id = 1
    node_list = {}  # type: typing.MutableMapping[str, int]
    for ecu in cluster.ecus:
        node = etree.Element('Node', name=ecu.name, id="%d" % element_id)
        root.append(node)
        node_list[ecu.name] = element_id
        element_id += 1
    for name in cluster:
        db = cluster[name]
        # Bus
        if 'Baudrate' in db.attributes:
            bus = etree.Element('Bus', baudrate=db.attributes['Baudrate'])
        else:
            bus = etree.Element('Bus')

        if not name:
            (path, ext) = os.path.splitext(f.name)
            name = path

        if name:
            bus.set("name", name)

        for frame in db.frames:  # type: canmatrix.Frame
            message = etree.Element(
                'Message',
                id="0x%03X" % frame.arbitration_id.id,
                name=frame.name,
                length=str(int(frame.size)))

            if frame.arbitration_id.extended == 1:
                message.set("format", "extended")
            if "GenMsgCycleTime" in db.frame_defines:
                cycle_time = frame.attribute("GenMsgCycleTime", db=db)
                if cycle_time is not None and int(cycle_time) > 0:
                    message.set("triggered", "true")
                    message.set("interval", "%d" % int(cycle_time))

            comment_elem = etree.Element('Notes')
            if frame.comment is not None:
                comment_elem.text = frame.comment
                message.append(comment_elem)

            producer = etree.Element('Producer')

            for transmitter in frame.transmitters:
                if transmitter in node_list and len(transmitter) > 1:
                    node_ref = etree.Element(
                        'NodeRef',
                        id=str(node_list[transmitter]))
                    producer.append(node_ref)
            if len(producer) > 0:
                message.append(producer)

            # check Multiplexor if present:
            value = None
            label_set = None
            multiplexor_elem = None
            for signal in frame.signals:
                if signal.multiplex is not None and signal.multiplex == 'Multiplexor':
                    multiplexor_elem = etree.Element(
                        'Multiplex',
                        name=signal.name,
                        offset=str(signal.get_startbit()),
                        length=str(int(signal.size)))
                    value = etree.Element('Value')
                    if float(signal.min) != 0:
                        value.set('min', "%g" % signal.min)  # type: ignore
                    if float(signal.max) != 1:
                        value.set('max', "%g" % signal.max)
                    label_set = etree.Element('LabelSet')
                    for valueVal, valName in sorted(signal.values.items(), key=lambda x: int(x[0])):
                        label = etree.Element(
                            'Label',
                            name=valName.replace('"', ''),
                            value=str(valueVal))
                        label_set.append(label)
            # multiplexor found
            if multiplexor_elem is not None:
                # ticker all potential muxgroups
                for i in range(0, 1 << int(multiplexor_elem.get('length'))):
                    empty = 0
                    muxgroup = etree.Element('MuxGroup', count=str(i))
                    for signal in frame.signals:
                        if signal.multiplex is not None and signal.multiplex == i:
                            sig = create_signal(signal, node_list, signal_type_enums)
                            muxgroup.append(sig)
                            empty = 1
                    if empty == 1:
                        multiplexor_elem.append(muxgroup)
                        multiplexor_elem.append(value)
                        multiplexor_elem.append(label_set)
                message.append(multiplexor_elem)

            # standard-signals:
            for signal in frame.signals:
                if signal.multiplex is None:
                    sig = create_signal(signal, node_list, signal_type_enums)
                    message.append(sig)

            bus.append(message)

        root.append(bus)
    f.write(etree.tostring(root, pretty_print=True))


def parse_signal(signal, mux, namespace, nodelist, float_factory):
    # type: (_Element, typing.Any, str, typing.Dict[str, str], typing.Callable) -> canmatrix.Signal
    start_bit = 0
    if 'offset' in signal.attrib:
        start_bit = int(signal.get('offset'))

    signal_size = 1
    if 'length' in signal.attrib:
        signal_size = int(signal.get('length'))

    is_little_endian = True
    if 'endianess' in signal.attrib:
        if signal.get('endianess') == 'big':
            is_little_endian = False

    unit = ""
    offset = float_factory('0')
    factor = float_factory('1')
    min_value = None
    max_value = None
    is_signed = False
    is_float = False

    values = signal.find('./' + namespace + 'Value')
    if values is not None:
        if 'type' in values.attrib:
            valuetype = values.get('type')
            if valuetype == "single" or valuetype == "double":
                is_float = True
            elif valuetype == "unsigned":
                is_signed = False
            else:
                is_signed = True

        if 'slope' in values.attrib:
            factor = values.get('slope')
        if 'intercept' in values.attrib:
            offset = values.get('intercept')
        if 'unit' in values.attrib:
            unit = values.get('unit')
        if 'min' in values.attrib:
            min_value = values.get('min')
        if 'max' in values.attrib:
            max_value = values.get('max')
    receiver = []
    consumers = signal.findall('./' + namespace + 'Consumer')
    for consumer in consumers:
        noderefs = consumer.findall('./' + namespace + 'NodeRef')
        for noderef in noderefs:
            receiver.append(nodelist[noderef.get('id')])

    new_sig = canmatrix.Signal(
        signal.get('name'),
        start_bit=int(start_bit),
        size=int(signal_size),
        is_little_endian=is_little_endian,
        is_signed=is_signed,
        factor=factor,
        offset=offset,
        unit=unit,
        receivers=receiver,
        is_float=is_float,
        multiplex=mux)

    if min_value is not None:
        new_sig.min = float_factory(min_value)
    if max_value is not None:
        new_sig.max = float_factory(max_value)

    new_sig.set_startbit(int(start_bit))

    notes = signal.findall('./' + namespace + 'Notes')
    comment = ""
    for note in notes:
        if note.text is not None:
            comment += note.text
            new_sig.add_comment(comment)

    labelsets = signal.findall('./' + namespace + 'LabelSet')
    for labelset in labelsets:
        labels = labelset.findall('./' + namespace + 'Label')
        for label in labels:
            name = label.get('name')
            value = label.get('value')
            new_sig.add_values(value, name)

    return new_sig


def load(f, **options):
    # type: (typing.IO, **typing.Any) -> typing.Dict[str, canmatrix.CanMatrix]
    float_factory = options.get("float_factory", default_float_factory)  # type: typing.Callable
    dbs = {}  # type: typing.Dict[str, canmatrix.CanMatrix]
    tree = etree.parse(f)
    root = tree.getroot()
    namespace = "{" + tree.xpath('namespace-uri(.)') + "}"

    node_list = {}
    nodes = root.findall('./' + namespace + 'Node')
    buses = root.findall('./' + namespace + 'Bus')

    counter = 0
    for bus in buses:
        db = canmatrix.CanMatrix()
        db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
        for node in nodes:
            db.ecus.append(canmatrix.Ecu(node.get('name')))
            node_list[node.get('id')] = node.get('name')

        messages = bus.findall('./' + namespace + 'Message')

        for message in messages:
            dlc = None
            # new_frame = Frame(int(message.get('id'), 16), message.get('name'), 1, None)
            new_frame = canmatrix.Frame(message.get('name'))

            if 'triggered' in message.attrib:
                new_frame.add_attribute("GenMsgCycleTime", message.get('interval'))

            if 'length' in message.attrib:
                dlc = int(message.get('length'))
                new_frame.size = dlc

            if 'format' in message.attrib and message.get('format') == "extended":
                new_frame.arbitration_id = canmatrix.ArbitrationId(int(message.get('id'), 16), extended=True)
            else:
                new_frame.arbitration_id = canmatrix.ArbitrationId(int(message.get('id'), 16), extended=False)

            multiplex = message.find('./' + namespace + 'Multiplex')
            if multiplex is not None:
                start_bit = 0
                if 'offset' in multiplex.attrib:
                    start_bit = int(multiplex.get('offset'))

                signal_size = 1
                if 'length' in multiplex.attrib:
                    signal_size = int(multiplex.get('length'))

                is_little_endian = True

                min_value = None
                max_value = None
                values = multiplex.find('./' + namespace + 'Value')
                if values is not None:
                    if 'min' in values.attrib:
                        min_value = float_factory(values.get('min'))
                    if 'max' in values.attrib:
                        max_value = float_factory(values.get('max'))

                unit = ""
                offset = float_factory('0')
                factor = float_factory('1')
                is_signed = False
                if 'type' in multiplex.attrib:
                    if multiplex.get('type') == 'signed':
                        is_signed = True

                receiver_names = []  # type: typing.List[str]
                consumers = multiplex.findall('./' + namespace + 'Consumer')
                for consumer in consumers:
                    node_refs = consumer.findall('./' + namespace + 'NodeRef')
                    for node_ref in node_refs:
                        receiver_names.append(node_list[node_ref.get('id')])
                new_signal = canmatrix.Signal(
                    multiplex.get('name'),
                    start_bit=int(start_bit),
                    size=int(signal_size),
                    is_little_endian=is_little_endian,
                    is_signed=is_signed,
                    factor=factor,
                    offset=offset,
                    unit=unit,
                    receivers=receiver_names,
                    multiplex='Multiplexor')

                if min_value is not None:
                    new_signal.min = min_value
                if max_value is not None:
                    new_signal.max = max_value

                if is_little_endian is False:
                    # motorola/big_endian set/convert startbit
                    new_signal.set_startbit(start_bit)
                notes = multiplex.findall('./' + namespace + 'Notes')
                comment = ""
                for note in notes:
                    comment += note.text
                new_signal.add_comment(comment)

                label_sets = multiplex.findall('./' + namespace + 'LabelSet')
                for label_set in label_sets:
                    labels = label_set.findall('./' + namespace + 'Label')
                    for label in labels:
                        name = label.get('name')
                        value = label.get('value')
                        new_signal.add_values(value, name)

                new_frame.add_signal(new_signal)

                mux_groups = multiplex.findall('./' + namespace + 'MuxGroup')
                for mux_group in mux_groups:
                    mux = mux_group.get('count')
                    signals = mux_group.findall('./' + namespace + 'Signal')
                    for signal in signals:
                        new_signal = parse_signal(signal, mux, namespace, node_list, float_factory)
                        new_frame.add_signal(new_signal)

            signals = message.findall('./' + namespace + 'Signal')

            producers = message.findall('./' + namespace + 'Producer')
            for producer in producers:
                node_refs = producer.findall('./' + namespace + 'NodeRef')
                for node_ref in node_refs:
                    new_frame.add_transmitter(node_list[node_ref.get('id')])
            for signal in signals:
                new_signal = parse_signal(signal, None, namespace, node_list, float_factory)
                new_frame.add_signal(new_signal)

            notes = message.findall('./' + namespace + 'Notes')
            comment = ""
            for note in notes:
                if note.text is not None:
                    comment += note.text
            new_frame.add_comment(comment)

            if dlc is None:
                new_frame.calc_dlc()
            else:
                new_frame.size = dlc

            new_frame.update_receiver()
            db.add_frame(new_frame)
        name = bus.get('name')
        if not name:
            name = "CAN%d" % counter
            counter += 1
        dbs[name] = db
    return dbs
