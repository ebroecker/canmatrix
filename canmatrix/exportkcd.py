from __future__ import absolute_import
from builtins import *
#!/usr/bin/env python


#Copyright (c) 2013, Eduard Broecker
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#DAMAGE.

#
# this script exports kcd-files from a canmatrix-object
# kcd-files are the can-matrix-definitions of the kayak (http://kayak.2codeornot2code.org/)

from lxml import etree
from .canmatrix import *

def createSignal(signal, nodeList):
    sig = etree.Element('Signal', name=signal._name, offset=str(signal.getLsbStartbit()))
    if signal._signalsize > 1:
        sig.set("length", str(signal._signalsize))
    if signal._is_little_endian == 0:
        sig.set('endianess',"little")

    notes = etree.Element('Notes')
    if signal._comment is not None:
        notes.text = signal._comment
    sig.append(notes)

    value = etree.Element('Value')
    if signal._is_signed:
        value.set('type',"signed")
    else:
        value.set('type',"unsigned")

    if float(signal._factor) != 1:
        value.set('slope',str("%g" % signal._factor))
    if float(signal._offset) != 0:
        value.set('intercept',str("%g" % signal._offset))
    if float(signal._min) != 0:
        value.set('min',str("{}".format(signal._min)))
    if float(signal._max) != 1:
        value.set('max',str("{}".format(signal._max)))
    if len(signal._unit) > 0:
        value.set('unit',signal._unit)
    sig.append(value)


    labelset = etree.Element('LabelSet')
    for valueVal,valName in sorted(signal._values.items(), key=lambda x: int(x[0])):
        label = etree.Element('Label', name=valName.replace('"',''), value=str(valueVal))
        labelset.append(label)
    sig.append(labelset)

    consumer = etree.Element('Consumer')
    for receiver in signal._receiver:
        if len(receiver) > 1 and receiver in nodeList:
            noderef = etree.Element('NodeRef', id=str(nodeList[receiver]))
            consumer.append(noderef)
            sig.append(consumer)
    return sig


def exportKcd(db, filename):
    # create XML
    root = etree.Element('NetworkDefinition')
    root.set("xmlns","http://kayak.2codeornot2code.org/1.0")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "schemaLocation", "Definition.xsd")


    #root.append(etree.Element('Document'))
    # another child with text

    child = etree.Element('Document')
    child.set("name","Some Document Name")
    child.text = 'some text'
    root.append(child)


    # Nodes:
    id = 1
    nodeList = {};
    for bu in db._BUs._list:
        node = etree.Element('Node', name=bu._name, id="%d" %id)
        root.append(node)
        nodeList[bu._name] = id;
        id += 1
    # Bus
    if 'Baudrate' in db._attributes:
        bus = etree.Element('Bus', baudrate=db._attributes['Baudrate'])
    else:
        bus = etree.Element('Bus')

    bus.set("name",filename)

    for frame in db._fl._list:
        message = etree.Element('Message', id="0x%03X" % frame._Id, name=frame._name, length = str(int(frame._Size)))

        if frame._extended == 1:
            message.set("format", "extended")
        if "GenMsgCycleTime" in frame._attributes:
            cycleTime = int(frame._attributes["GenMsgCycleTime"])
            if cycleTime > 0:
                message.set("triggered", "true")
                message.set("interval", "%d" % cycleTime)

        producer = etree.Element('Producer')

        for transmitter in frame._Transmitter:
            if len(transmitter) > 1 and transmitter in nodeList:
                noderef = etree.Element('NodeRef', id=str(nodeList[transmitter]))
                producer.append(noderef)
        message.append(producer)

        comment = etree.Element('Notes')
        if frame._comment is not None:
            comment.text = frame._comment
            message.append(comment)


        # standard-signals:
        for signal in frame._signals:
            if signal._multiplex is None:
                sig = createSignal(signal, nodeList)
                message.append(sig)

        # check Multiplexor if present:
        multiplexor = None
        for signal in frame._signals:
            if signal._multiplex is not None and signal._multiplex == 'Multiplexor':
                multiplexor = etree.Element('Multiplex', name=signal._name, offset=str(signal.getLsbStartbit()), length=str(int(signal._signalsize)))
                value = etree.Element('Value')
                if float(signal._min) != 0:
                    value.set('min', "%g" % signal._min)
                if float(signal._max) != 1:
                    value.set('max', "%g" % signal._max)
                multiplexor.append(value)
                labelset = etree.Element('LabelSet')
                for valueVal,valName in sorted(signal._values.items(), key=lambda x: int(x[0])):
                    label = etree.Element('Label', name=valName.replace('"',''), value=str(valueVal))
                    labelset.append(label)
                multiplexor.append(labelset)



        # multiplexor found
        if multiplexor is not None:
            # ticker all potential muxgroups
            for i in range(0,1<<int(multiplexor.get('length'))):
                empty = 0
                muxgroup = etree.Element('MuxGroup', count=str(i))
                for signal in frame._signals:
                    if signal._multiplex is not None and signal._multiplex == i:
                        sig = createSignal(signal, nodeList)
                        muxgroup.append(sig)
                        empty = 1
                if empty == 1:
                    multiplexor.append(muxgroup)
            message.append(multiplexor)

        bus.append(message)

    root.append(bus)
    f = open(filename,"wb");
    f.write(etree.tostring(root, pretty_print=True))
