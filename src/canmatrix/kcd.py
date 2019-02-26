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
from builtins import *
from lxml import etree
import canmatrix
from .cancluster import *
import os
import re
import math
import decimal
default_float_factory = decimal.Decimal

clusterExporter = 1
clusterImporter = 1
def create_signal(signal, nodeList, typeEnums):
    xml_signal = etree.Element(
        'Signal',
        name=signal.name,
        offset=str(
            signal.get_startbit()))
    if signal.size > 1:
        xml_signal.set("length", str(signal.size))
    if signal.is_little_endian == 0:
        xml_signal.set('endianess', "big")

    comment = signal.comment

    if len(signal.attributes.items()) > 0:
        if comment is None:
            comment = ''
        else:
            comment += '\n'

    for attrib, val in sorted(signal.attributes.items()):
        try:
            if attrib in typeEnums and int(val) < len(typeEnums[attrib]):
                val = typeEnums[attrib][int(val)]
            comment += ("\n" + attrib + ': ' + val)
        except:
            pass

    if comment is not None:
        notes = etree.Element('Notes')
        notes.text = comment
        xml_signal.append(notes)

    consumer = etree.Element('Consumer')
    for receiver in signal.receivers:
        if receiver in nodeList and len(receiver) > 1:
            noderef = etree.Element('NodeRef', id=str(nodeList[receiver]))
            consumer.append(noderef)
        if consumer.__len__() > 0:
            xml_signal.append(consumer)
    value = etree.Element('Value')
    if signal.is_float:
        if signal.signalsize > 32:
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

    if len(signal.values) > 0:
        labelset = etree.Element('LabelSet')
        for valueVal, valName in sorted(
                signal.values.items(), key=lambda x: int(x[0])):
            label = etree.Element(
                'Label', name=valName.replace(
                    '"', ''), value=str(valueVal))
            labelset.append(label)
        xml_signal.append(labelset)

    return xml_signal


def dump(dbs, f, **options):

    signalTypeEnums = {}
    canClust = canCluster(dbs)
    for name in canClust:
        db = canClust[name]
        for (typename, define) in list(db.signal_defines.items()):
            defines = re.split(r"\s+", define.definition)
            define_type = defines[0]
            if define_type != 'ENUM':
                continue
            defines = defines[1].strip('"')
            defines = defines.split('","')
            signalTypeEnums[typename] = defines

    # create XML
    root = etree.Element('NetworkDefinition')
    root.set("xmlns", "http://kayak.2codeornot2code.org/1.0")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "schemaLocation", "Definition.xsd")

    # root.append(etree.Element('Document'))
    # another child with text

    child = etree.Element('Document')
    child.set("name", "Some Document Name")
    child.text = 'some text'
    root.append(child)

    # Nodes:
    id = 1
    nodeList = {}
#    for name in dbs:
#        db = dbs[name]
    for bu in canClust.boardUnits:
        node = etree.Element('Node', name=bu.name, id="%d" % id)
        root.append(node)
        nodeList[bu.name] = id
        id += 1
    for name in canClust:
        db = canClust[name]
        # Bus
        if 'Baudrate' in db.attributes:
            bus = etree.Element('Bus', baudrate=db.attributes['Baudrate'])
        else:
            bus = etree.Element('Bus')

        if len(name) == 0:
            (path, ext) = os.path.splitext(f.name)
            name = path

        if len(name) > 0:
            bus.set("name", name)

        for frame in db.frames:
            message = etree.Element('Message', id="0x%03X" %
                                    frame.arbitration_id.id, name=frame.name, length=str(int(frame.size)))

            if frame.arbitration_id.extended == 1:
                message.set("format", "extended")
            if "GenMsgCycleTime" in db.frame_defines:
                cycleTime = frame.attribute("GenMsgCycleTime", db=db)
                if cycleTime is not None and int(cycleTime) > 0:
                    message.set("triggered", "true")
                    message.set("interval", "%d" % int(cycleTime))

            comment = etree.Element('Notes')
            if frame.comment is not None:
                comment.text = frame.comment
                message.append(comment)


            producer = etree.Element('Producer')

            for transmitter in frame.transmitters:
                if transmitter in nodeList and len(transmitter) > 1:
                    noderef = etree.Element(
                        'NodeRef', id=str(
                            nodeList[transmitter]))
                    producer.append(noderef)
            if producer.__len__() > 0:
                message.append(producer)

            # check Multiplexor if present:
            value = None
            labelset = None
            multiplexor = None
            for signal in frame.signals:
                if signal.multiplex is not None and signal.multiplex == 'Multiplexor':
                    multiplexor = etree.Element('Multiplex', name=signal.name, offset=str(
                        signal.get_startbit()), length=str(int(signal.size)))
                    value = etree.Element('Value')
                    if float(signal.min) != 0:
                        value.set('min', "%g" % signal.min)
                    if float(signal.max) != 1:
                        value.set('max', "%g" % signal.max)
                    labelset = etree.Element('LabelSet')
                    for valueVal, valName in sorted(
                            signal.values.items(), key=lambda x: int(x[0])):
                        label = etree.Element(
                            'Label', name=valName.replace(
                                '"', ''), value=str(valueVal))
                        labelset.append(label)
           # multiplexor found
            if multiplexor is not None:
                # ticker all potential muxgroups
                for i in range(0, 1 << int(multiplexor.get('length'))):
                    empty = 0
                    muxgroup = etree.Element('MuxGroup', count=str(i))
                    for signal in frame.signals:
                        if signal.multiplex is not None and signal.multiplex == i:
                            sig = create_signal(
                                signal, nodeList, signalTypeEnums)
                            muxgroup.append(sig)
                            empty = 1
                    if empty == 1:
                        multiplexor.append(muxgroup)
                        multiplexor.append(value)
                        multiplexor.append(labelset)
                message.append(multiplexor)


            # standard-signals:
            for signal in frame.signals:
                if signal.multiplex is None:
                    sig = create_signal(signal, nodeList, signalTypeEnums)
                    message.append(sig)


            bus.append(message)

        root.append(bus)
    f.write(etree.tostring(root, pretty_print=True))

def parse_signal(signal, mux, namespace, nodelist, float_factory):
    startbit = 0
    if 'offset' in signal.attrib:
        startbit = signal.get('offset')

    signalsize = 1
    if 'length' in signal.attrib:
        signalsize = signal.get('length')

    is_little_endian = True
    if 'endianess' in signal.attrib:
        if signal.get('endianess') == 'big':
            is_little_endian = False

    unit = ""
    offset = float_factory('0')
    factor = float_factory('1')
    min = None
    max = None
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
            min = values.get('min')
        if 'max' in values.attrib:
            max = values.get('max')
    receiver = []
    consumers = signal.findall('./' + namespace + 'Consumer')
    for consumer in consumers:
        noderefs = consumer.findall('./' + namespace + 'NodeRef')
        for noderef in noderefs:
            receiver.append(nodelist[noderef.get('id')])

    new_sig = canmatrix.Signal(signal.get('name'),
                    start_bit=int(startbit),
                    size=int(signalsize),
                    is_little_endian=is_little_endian,
                    is_signed=is_signed,
                    factor=factor,
                    offset=offset,
                    unit=unit,
                    receivers=receiver,
                    is_float = is_float,
                    multiplex=mux)

    if min is not None:
        new_sig.min = float_factory(min)
    if max is not None:
        new_sig.max = float_factory(max)

    new_sig.set_startbit(int(startbit))

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
    float_factory = options.get("float_factory", default_float_factory)
    dbs = {}
    tree = etree.parse(f)
    root = tree.getroot()
    namespace = "{" + tree.xpath('namespace-uri(.)') + "}"

    nodelist = {}
    nodes = root.findall('./' + namespace + 'Node')

    busses = root.findall('./' + namespace + 'Bus')

    counter = 0
    for bus in busses:
        db = canmatrix.CanMatrix()
        db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
        for node in nodes:
            db.BUs.add(canmatrix.ecu(node.get('name')))
            nodelist[node.get('id')] = node.get('name')

        messages = bus.findall('./' + namespace + 'Message')

        for message in messages:
            dlc = None
            #new_frame = Frame(int(message.get('id'), 16), message.get('name'), 1, None)
            new_frame = canmatrix.Frame(message.get('name'))

            if 'triggered' in message.attrib:
                new_frame.add_attribute("GenMsgCycleTime", message.get('interval'))

            if 'length' in message.attrib:
                dlc = int(message.get('length'))
                new_frame.size = dlc

            if 'format' in message.attrib and message.get('format') == "extended":
                new_frame.arbitration_id = canmatrix.ArbitrationId(int(message.get('id'), 16), extended = True)
            else:
                new_frame.arbitration_id = canmatrix.ArbitrationId(int(message.get('id'), 16), extended = False)


            multiplex = message.find('./' + namespace + 'Multiplex')
            if multiplex is not None:
                startbit = 0
                if 'offset' in multiplex.attrib:
                    startbit = multiplex.get('offset')

                signalsize = 1
                if 'length' in multiplex.attrib:
                    signalsize = multiplex.get('length')

                is_little_endian = True

                min = None
                max = None
                values = multiplex.find('./' + namespace + 'Value')
                if values is not None:
                    if 'min' in values.attrib:
                        min = float_factory(values.get('min'))
                    if 'max' in values.attrib:
                        max = float_factory(values.get('max'))

                unit = ""
                offset = float_factory('0')
                factor = float_factory('1')
                is_signed = False
                if 'type' in multiplex.attrib:
                    if multiplex.get('type') == 'signed':
                        is_signed = True

                receiver = []
                consumers = multiplex.findall('./' + namespace + 'Consumer')
                for consumer in consumers:
                    noderefs = consumer.findall('./' + namespace + 'NodeRef')
                    for noderef in noderefs:
                        receiver.append(nodelist[noderef.get('id')])
                newSig = canmatrix.Signal(multiplex.get('name'),
                                start_bit=int(startbit),
                                size=int(signalsize),
                                is_little_endian=is_little_endian,
                                is_signed=is_signed,
                                factor=factor,
                                offset=offset,
                                unit=unit,
                                receivers=receiver,
                                multiplex='Multiplexor')

                if min is not None:
                    newSig.min = min
                if max is not None:
                    newSig.max = max

                if is_little_endian == False:
                    # motorola/big_endian set/convert startbit
                    newSig.set_startbit(startbit)
                notes = multiplex.findall('./' + namespace + 'Notes')
                comment = ""
                for note in notes:
                    comment += note.text
                newSig.add_comment(comment)

                labelsets = multiplex.findall('./' + namespace + 'LabelSet')
                for labelset in labelsets:
                    labels = labelset.findall('./' + namespace + 'Label')
                    for label in labels:
                        name = label.get('name')
                        value = label.get('value')
                        newSig.add_values(value, name)

                new_frame.add_signal(newSig)

                muxgroups = multiplex.findall('./' + namespace + 'MuxGroup')
                for muxgroup in muxgroups:
                    mux = muxgroup.get('count')
                    signales = muxgroup.findall('./' + namespace + 'Signal')
                    for signal in signales:
                        newSig = parse_signal(signal, mux, namespace, nodelist, float_factory)
                        new_frame.add_signal(newSig)

            signales = message.findall('./' + namespace + 'Signal')

            producers = message.findall('./' + namespace + 'Producer')
            for producer in producers:
                noderefs = producer.findall('./' + namespace + 'NodeRef')
                for noderef in noderefs:
                    new_frame.add_transmitter(nodelist[noderef.get('id')])
            for signal in signales:
                newSig = parse_signal(signal, None, namespace, nodelist, float_factory)
                new_frame.add_signal(newSig)

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
