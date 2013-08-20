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
# this script imports dbf-files in a canmatrix-object
# dbf-files are the can-matrix-definitions of the busmaster-project (http://rbei-etas.github.io/busmaster/)
#

from canmatrix import *
import re

#TODO support for [START_PARAM_NODE_RX_SIG]
#TODO support for [START_PARAM_NODE_TX_MSG]

dbfImportEncoding = 'iso-8859-1'

def decodeDefine(line):
	(define, valueType, value) = line.split(',',2)			 
	valueType = valueType.strip()
	if valueType == "INT" or valueType == "HEX":
		(Min, Max, default) = value.split(',',2)
		myDef = valueType + ' ' + Min.strip() + ' ' + Max.strip()
		default = default.strip()
	elif valueType == "ENUM":
		(enums, default) = value.rsplit(',',1)
		myDef = valueType + "  " + enums[1:]
	elif valueType == "STRING":
		myDef = valueType 
		default = value
	else:
		print line

	return define[1:-1], myDef, default


def importDbf(filename):

	db = CanMatrix()
	f = open(filename,"r")

	mode = ''
	for line in f:
		line = line.strip()
		
		if mode == 'SignalDescription':
			if line.startswith("[END_DESC_SIG]") or line.startswith("[END_DESC]"):
				mode = ''
			else:
				(boId, temS, SignalName, comment) = line.split(' ',3)	
				comment = comment.replace('"','').replace(';','').decode(dbfImportEncoding)		
				db.frameById(int(boId)).signalByName(SignalName).addComment(comment)

		if mode == 'BUDescription':
			if line.startswith("[END_DESC_NODE]") or line.startswith("[END_DESC]"):
				mode = ''
			else:
				(BUName, comment) = line.split(' ',1)	
				comment = comment.replace('"','').replace(';','').decode(dbfImportEncoding)		
				db._BUs.byName(BUName).addComment(comment)

		if mode == 'FrameDescription':
			if line.startswith("[END_DESC_MSG]") or line.startswith("[END_DESC]"):
				mode = ''
			else:
				(boId, temS, comment) = line.split(' ',2)	
				comment = comment.replace('"','').replace(';','').decode(dbfImportEncoding)		
				db.frameById(int(boId)).addComment(comment)

		elif mode == 'ParamMsgVal':
			if line.startswith("[END_PARAM_MSG_VAL]"):
				mode = ''
			else:
				(boId, temS, attrib, value) = line.split(',',3)	
				db.frameById(int(boId)).addAttribute(attrib.replace('"',''), value[1:-1])

		elif mode == 'ParamNodeVal':
			if line.startswith("[END_PARAM_NODE_VAL]"):
				mode = ''
			else:
				(bu, attrib, value) = line.split(',',2)	
				db._BUs.byName(bu).addAttribute(attrib.replace('"',''), value[1:-1])

		elif mode == 'ParamNetVal':
			if line.startswith("[END_PARAM_NET_VAL]"):
				mode = ''
			else:
				(attrib, value) = line.split(',',1)	
				db.addAttribute(attrib.replace('"',''), value[1:-1])

		elif mode == 'ParamSigVal':
			if line.startswith("[END_PARAM_SIG_VAL]"):
				mode = ''
			else:				
				(boId, temS, SignalName, attrib, value) = line.split(',',4)			 
				db.frameById(int(boId)).signalByName(SignalName).addAttribute(attrib.replace('"',''), value[1:-1])

		elif mode == 'ParamSig':
			if line.startswith("[END_PARAM_SIG]"):
				mode = ''
			else:
				(name, define, default) = decodeDefine(line)
				db.addSignalDefines(name, define)
				db.addDefineDefault(name, default)

		elif mode == 'ParamMsg':
			if line.startswith("[END_PARAM_MSG]"):
				mode = ''
			else:
				(name, define, default) = decodeDefine(line)
				db.addFrameDefines(name, define)
				db.addDefineDefault(name, default)

		elif mode == 'ParamNode':
			if line.startswith("[END_PARAM_NODE]"):
				mode = ''
			else:
				(name, define, default) = decodeDefine(line)
				db.addBUDefines(name, define)
				db.addDefineDefault(name, default)

		elif mode == 'ParamNet':
			if line.startswith("[END_PARAM_NET]"):
				mode = ''
			else:
				(name, define, default) = decodeDefine(line)
				db.addGlobalDefines(name, define)
				db.addDefineDefault(name, default)
		
		else:	
			if line.startswith("[START_DESC_SIG]"):
				mode = 'SignalDescription'

			if line.startswith("[START_DESC_MSG]"):
				mode = 'FrameDescription'

			if line.startswith("[START_DESC_NODE]"):
				mode = 'BUDescription'

			if line.startswith("[START_PARAM_NODE_VAL]"):
				mode = 'ParamNodeVal'

			if line.startswith("[START_PARAM_NET_VAL]"):
				mode = 'ParamNetVal'

			if line.startswith("[START_PARAM_MSG_VAL]"):
				mode = 'ParamMsgVal'

			if line.startswith("[START_PARAM_SIG_VAL]"):
				mode = 'ParamSigVal'
	
			if line.startswith("[START_PARAM_SIG]"):
				mode = 'ParamSig'
			if line.startswith("[START_PARAM_MSG]"):
				mode = 'ParamMsg'
			if line.startswith("[START_PARAM_NODE]"):
				mode = 'ParamNode'
			if line.startswith("[START_PARAM_NET]"):
				mode = 'ParamNet'


			if line.startswith("[START_MSG]"):
				temstr = line.strip()[11:].strip()
				(name, Id, size, nSignals, extended, motIntl ,transmitter) = temstr.split(',') 
				newBo = db._fl.addFrame(Frame(int(Id), name, size, transmitter))
				if extended == 'X':
					newBo._extended = 1
		
			if line.startswith("[NODE]"):
				temstr = line.strip()[6:].strip()
				boList = temstr.split(',')
				for bo in boList:			
					db._BUs.add(BoardUnit(bo))

			if line.startswith("[START_SIGNALS]"):
				temstr = line.strip()[15:].strip()
				(name, size, startbyte, startbit, sign, Min, Max, byteorder, offset, factor, unit, multiplex, reciever) = temstr.split(',',12)

						
				if multiplex == 'M':
					multiplex = 'Multiplexor'
				elif multiplex.strip().__len__() > 0:
					multiplex = int(multiplex[1:])
				else:
					multiplex = None

				sign = '+'
				newSig = newBo.addSignal(Signal(name, startbit, size, byteorder, sign, factor, offset, Min, Max, unit.decode(dbfImportEncoding), reciever.split(','), multiplex))

			if line.startswith("[VALUE_DESCRIPTION]"):
				temstr = line.strip()[19:].strip()
				regexp = re.compile("\"(.+)\" *, *(.+)")		
				temp = regexp.match(temstr)
				
				if temp:
					name = temp.group(1)
					value = temp.group(2)
					newSig.addValues(value, name.decode(dbfImportEncoding))


	return db


