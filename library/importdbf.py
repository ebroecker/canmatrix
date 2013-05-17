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

#TODO support for [START_PARAM_NET]
#TODO support for [START_PARAM_NODE]
#TODO support for [START_PARAM_MSG]
#TODO support for [START_PARAM_SIG]
#TODO support for [START_PARAM_NODE_RX_SIG]
#TODO support for [START_PARAM_NODE_TX_MSG]
#TODO support for [START_PARAM_VAL]
#TODO support for [START_PARAM_NET_VAL]
#TODO support for [START_PARAM_NODE_VAL]

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
				db._bl.byId(int(boId)).signalByName(SignalName).addComment(comment.replace('"','').replace(';',''))

		elif mode == 'ParamMsgVal':
			if line.startswith("[END_PARAM_MSG_VAL]"):
				mode = ''
			else:
				(boId, temS, attrib, value) = line.split(',',3)			
				db._bl.byId(int(boId)).addAttribute(attrib.replace('"',''), value)

		elif mode == 'ParamSigVal':
			if line.startswith("[END_PARAM_SIG_VAL]"):
				mode = ''
			else:
				(boId, temS, SignalName, attrib, value) = line.split(',',4)			
				db._bl.byId(int(boId)).signalByName(SignalName).addAttribute(attrib.replace('"',''), value)
		
		else:	
			if line.startswith("[START_DESC_SIG]"):
				mode = 'SignalDescription'

			if line.startswith("[START_PARAM_MSG_VAL]"):
				mode = 'ParamMsgVal'

			if line.startswith("[START_PARAM_SIG_VAL]"):
				mode = 'ParamSigVal'
	
			if line.startswith("[START_MSG]"):
				temstr = line.strip()[11:].strip()
				(name, Id, size, nSignals, extended, motIntl ,transmitter) = temstr.split(',') 
				newBo = db._bl.addBotschaft(Botschaft(int(Id), name, size, transmitter))
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
				else:
					multiplex = multiplex[1:]

				sign = '+'
				newSig = newBo.addSignal(Signal(name, startbit, size, byteorder, sign, factor, offset, Min, Max, unit, reciever.split(','), multiplex))

			if line.startswith("[VALUE_DESCRIPTION]"):
				temstr = line.strip()[19:].strip()
				(name, value) = temstr.split(',')
				newSig.addValues(value, name)

	return db


