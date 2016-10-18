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
from .canmatrix import *
from .cancluster import *
import os
import re
import math

clusterExporter = 1
clusterImporter = 1


def createSignal(signal, nodeList, typeEnums):
    sig = etree.Element(
        'Signal',
        name=signal.name,
        offset=str(
            signal.getStartbit()))
    if signal.signalsize > 1:
        sig.set("length", str(signal.signalsize))
    if signal.is_little_endian == 0:
        sig.set('endianess', "big")

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
        sig.append(notes)

    value = etree.Element('Value')
    if signal.is_signed:
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
        sig.append(value)

    if len(signal.values) > 0:
        labelset = etree.Element('LabelSet')
        for valueVal, valName in sorted(
                signal.values.items(), key=lambda x: int(x[0])):
            label = etree.Element(
                'Label', name=valName.replace(
                    '"', ''), value=str(valueVal))
            labelset.append(label)
        sig.append(labelset)

    consumer = etree.Element('Consumer')
    for receiver in signal.receiver:
        if len(receiver) > 1 and receiver in nodeList:
            noderef = etree.Element('NodeRef', id=str(nodeList[receiver]))
            consumer.append(noderef)
        if consumer.__len__() > 0:
            sig.append(consumer)
    return sig


def dump(dbs, f, **options):
    signalTypeEnums = {}
    canClust = canCluster(dbs)
    for name in canClust:
        db = canClust[name]
        for (typename, define) in list(db.signalDefines.items()):
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

#        if len(name) == 0:
#            (path, ext) = os.path.splitext(filename)
#            busName = path
#        else:
#            busName = name

        if len(name) > 0:
            bus.set("name", name)

        for frame in db.frames:
            message = etree.Element('Message', id="0x%03X" %
                                    frame.id, name=frame.name, length=str(int(frame.size)))

            if frame.extended == 1:
                message.set("format", "extended")
            if "GenMsgCycleTime" in frame.attributes:
                cycleTime = int(frame.attributes["GenMsgCycleTime"])
                if cycleTime > 0:
                    message.set("triggered", "true")
                    message.set("interval", "%d" % cycleTime)

            producer = etree.Element('Producer')

            for transmitter in frame.transmitter:
                if len(transmitter) > 1 and transmitter in nodeList:
                    noderef = etree.Element(
                        'NodeRef', id=str(
                            nodeList[transmitter]))
                    producer.append(noderef)
            if producer.__len__() > 0:
                message.append(producer)

            comment = etree.Element('Notes')
            if frame.comment is not None:
                comment.text = frame.comment
                message.append(comment)

            # standard-signals:
            for signal in frame.signals:
                if signal.multiplex is None:
                    sig = createSignal(signal, nodeList, signalTypeEnums)
                    message.append(sig)

            # check Multiplexor if present:
            multiplexor = None
            for signal in frame.signals:
                if signal.multiplex is not None and signal.multiplex == 'Multiplexor':
                    multiplexor = etree.Element('Multiplex', name=signal.name, offset=str(
                        signal.getStartbit()), length=str(int(signal.signalsize)))
                    value = etree.Element('Value')
                    if float(signal.min) != 0:
                        value.set('min', "%g" % signal.min)
                    if float(signal.max) != 1:
                        value.set('max', "%g" % signal.max)
                    multiplexor.append(value)
                    labelset = etree.Element('LabelSet')
                    for valueVal, valName in sorted(
                            signal.values.items(), key=lambda x: int(x[0])):
                        label = etree.Element(
                            'Label', name=valName.replace(
                                '"', ''), value=str(valueVal))
                        labelset.append(label)
                    multiplexor.append(labelset)

            # multiplexor found
            if multiplexor is not None:
                # ticker all potential muxgroups
                for i in range(0, 1 << int(multiplexor.get('length'))):
                    empty = 0
                    muxgroup = etree.Element('MuxGroup', count=str(i))
                    for signal in frame.signals:
                        if signal.multiplex is not None and signal.multiplex == i:
                            sig = createSignal(
                                signal, nodeList, signalTypeEnums)
                            muxgroup.append(sig)
                            empty = 1
                    if empty == 1:
                        multiplexor.append(muxgroup)
                message.append(multiplexor)

            bus.append(message)

        root.append(bus)
    f.write(etree.tostring(root, pretty_print=True))


def parseSignal(signal, mux, namespace, nodelist):
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
    offset = 0
    factor = 1
    min = None
    max = None
    is_signed = False

    values = signal.find('./' + namespace + 'Value')
    if values is not None:
        if 'type' in values.attrib:
            valuetype = values.get('type')
            if valuetype == "unsigned":
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

    newSig = Signal(signal.get('name'),
                    startBit=startbit,
                    signalSize=signalsize,
                    is_little_endian=is_little_endian,
                    is_signed=is_signed,
                    factor=factor,
                    offset=offset,
                    min=min,
                    max=max,
                    unit=unit,
                    receiver=receiver,
                    multiplex=mux)
    newSig.setStartbit(int(startbit))

    notes = signal.findall('./' + namespace + 'Notes')
    comment = ""
    for note in notes:
        if note.text is not None:
            comment += note.text
            newSig.addComment(comment)

    labelsets = signal.findall('./' + namespace + 'LabelSet')
    for labelset in labelsets:
        labels = labelset.findall('./' + namespace + 'Label')
        for label in labels:
            name = label.get('name')
            value = label.get('value')
            newSig.addValues(value, name)

    return newSig


def load(f, **options):
    dbs = {}
    tree = etree.parse(f)
    root = tree.getroot()
    namespace = "{" + tree.xpath('namespace-uri(.)') + "}"

    nodelist = {}
    nodes = root.findall('./' + namespace + 'Node')

    busses = root.findall('./' + namespace + 'Bus')
    for bus in busses:
        db = CanMatrix()
        db.addFrameDefines("GenMsgCycleTime", 'INT 0 65535')
        for node in nodes:
            db._BUs.add(BoardUnit(node.get('name')))
            nodelist[node.get('id')] = node.get('name')

        messages = bus.findall('./' + namespace + 'Message')

        for message in messages:
            dlc = None
            #newBo = Frame(int(message.get('id'), 16), message.get('name'), 1, None)
            newBo = Frame(message.get('name'), Id=int(message.get('id'), 16))

            if 'triggered' in message.attrib:
                newBo.addAttribute("GenMsgCycleTime", message.get('interval'))

            if 'length' in message.attrib:
                dlc = int(message.get('length'))
                newBo.size = dlc

            if 'format' in message.attrib:
                if message.get('format') == "extended":
                    newBo.extended = 1

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
                        min = values.get('min')
                    if 'max' in values.attrib:
                        max = values.get('max')

                unit = ""
                offset = 0
                factor = 1
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

                newSig = Signal(multiplex.get('name'),
                                startBit=startbit,
                                signalSize=signalsize,
                                is_little_endian=is_little_endian,
                                is_signed=is_signed,
                                factor=factor,
                                offset=offset,
                                min=min,
                                max=max,
                                unit=unit,
                                receiver=receiver,
                                multiplex='Multiplexor')

                if is_little_endian == False:
                    # motorola/big_endian set/convert startbit
                    newSig.setStartbit(startbit)
                notes = multiplex.findall('./' + namespace + 'Notes')
                comment = ""
                for note in notes:
                    comment += note.text
                newSig.addComment(comment)

                labelsets = multiplex.findall('./' + namespace + 'LabelSet')
                for labelset in labelsets:
                    labels = labelset.findall('./' + namespace + 'Label')
                    for label in labels:
                        name = label.get('name')
                        value = label.get('value')
                        newSig.addValues(value, name)

                newBo.addSignal(newSig)

                muxgroups = multiplex.findall('./' + namespace + 'MuxGroup')
                for muxgroup in muxgroups:
                    mux = muxgroup.get('count')
                    signales = muxgroup.findall('./' + namespace + 'Signal')
                    for signal in signales:
                        newSig = parseSignal(signal, mux, namespace, nodelist)
                        newBo.addSignal(newSig)

            signales = message.findall('./' + namespace + 'Signal')

            producers = message.findall('./' + namespace + 'Producer')
            for producer in producers:
                noderefs = producer.findall('./' + namespace + 'NodeRef')
                for noderef in noderefs:
                    newBo.addTransmitter(nodelist[noderef.get('id')])

            for signal in signales:
                newSig = parseSignal(signal, None, namespace, nodelist)
                newBo.addSignal(newSig)

            notes = message.findall('./' + namespace + 'Notes')
            comment = ""
            for note in notes:
                if note.text is not None:
                    comment += note.text
            newBo.addComment(comment)

            if dlc is None:
                newBo.calcDLC()
            else:
                newBo.size = dlc

            newBo.updateReceiver()
            db._fl.addFrame(newBo)
        dbs[bus.get('name')] = db
    return dbs
