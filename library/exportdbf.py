#!/usr/bin/env python
from lxml import etree
from canmatrix import *

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
# this script exports dbf-files from a canmatrix-object
# dbf-files are the can-matrix-definitions of the busmaster-project (http://rbei-etas.github.io/busmaster/)


def exportDbf(db, filename):
	f = open(filename,"w")


	header = """//******************************BUSMASTER Messages and signals Database ******************************//

[DATABASE_VERSION] 1.3

[PROTOCOL] CAN

[BUSMASTER_VERSION] [1.7.2]
[NUMBER_OF_MESSAGES] """

	f.write( header + str(len(db._bl._liste)) + "\n")

	#Botschaften
	for bo in db._bl._liste:
	#Name unMsgId m_ucLength m_ucNumOfSignals m_cDataFormat m_cFrameFormat? m_txNode
	#m_cDataFormat If 1 dataformat Intel, 0- Motorola -- immer 1 original Converter macht das nach anzahl entsprechender Signale
	#cFrameFormat Standard 'S' Extended 'X'
		extended = 'S'
		if bo._extended == 1:
			extended = 'X'	
		f.write("[START_MSG] " + bo._name + ",%d,%d,%d,1,%c," % (bo._Id, bo._Size, len(bo._signals), extended))
		if bo._Transmitter.__len__() == 0:
			bo._Transmitter = ["Vector__XXX"]
#DBF does not support multiple Transmitters
		f.write( bo._Transmitter[0] + "\n")

		for signal in bo._signals:
	# m_acName ucLength m_ucWhichByte m_ucStartBit
	#m_ucDataFormat m_fOffset m_fScaleFactor m_acUnit m_acMultiplex m_rxNode
			#m_ucDataFormat		
			whichbyte = int(signal._startbit / 8 + 1)
			sign = 'S'
		
			if signal._valuetype == '+':
				sign = 'U'
			f.write("[START_SIGNALS] " + signal._name + ",%d,%d,%d,%c,%g,%g" % (signal._signalsize,whichbyte,signal._startbit,sign,signal._min,signal._max))

			f.write(",%d,%g,%g" % (signal._byteorder, signal._offset, signal._factor))
			multiplex = ""
			if signal._multiplex is not None:
				if signal._multiplex == 'Multiplexor':
					multiplex = 'M'
				else:			
			 		multiplex = 'm' + str(signal._multiplex)

			f.write("," + signal._unit.encode('CP1253') + ",%s,"%multiplex + ','.join(signal._reciever) + "\n")

			if len(signal._values) > 0:
				for attrib,val in signal._values.items():
					f.write('[VALUE_DESCRIPTION] ' + val + "," + str(attrib) + "\n")
			

		f.write("[END_MSG]\n\n")

	#Boardunits
	f.write ("[NODE] ")
	count = 1
	for bu in db._BUs._liste:
		f.write(bu._name)
		if count < len(db._BUs._liste): 	
			f.write(",")
		count += 1
	f.write("\n")

	#signalbezeichnungen
	f.write("[START_DESC]\n\n")
	f.write("[START_DESC_SIG]\n")
	for bo in db._bl._liste:
		for signal in bo._signals:
			f.write("%d S " % bo._Id + signal._name  + ' "' + signal._comment.encode('CP1253') + '";\n') 
	f.write("[END_DESC_SIG]\n")
	f.write("[END_DESC]\n\n")

	f.write("[START_PARAM]\n")
	f.write("[START_PARAM_VAL]\n")

	#TODO db-parameter sind nicht ordendlich im Objekt abgelegt
	#f.write("[START_PARAM_NET]\n")
	#for attrib,val in db._attributes.items():
	#	f.write('"' + attrib + '" ' + ' ' + val  + ';\n')
	#f.write("[END_PARAM_NET]\n")
	#BA_DEF_DEF fehlt in Datenbasis


	#boardunit-attributes:
	f.write("[START_PARAM_NODE_VAL]\n")
	for bu in db._BUs._liste:
		for attrib,val in bu._attributes.items():
			f.write(bu._name + ',' + attrib + ','  + val  + '\n')
	f.write("[END_PARAM_NODE_VAL]\n")


	#messages-attributes:
	f.write("[START_PARAM_MSG_VAL]\n")
	for bo in db._bl._liste:
		for attrib,val in bo._attributes.items():
			f.write( str(bo._Id) + ',S,' + attrib + ','  + val  + '\n')
	f.write("[END_PARAM_MSG_VAL]\n")

	#signal-attributes:
	f.write("[START_PARAM_SIG_VAL]\n")
	for bo in db._bl._liste:
		for signal in bo._signals:
			for attrib,val in signal._attributes.items():
				f.write( str(bo._Id) + ',S,' + attrib  +  ',' + val  + '\n')
	f.write("[END_PARAM_SIG_VAL]\n")
	f.write("[END_PARAM_VAL]\n")
