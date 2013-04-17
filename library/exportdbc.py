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
# this script exports dbc-files from a canmatrix-object
# dbc-files are the can-matrix-definitions of the CanOe (Vector Informatic)
#  NOT supported BA_DEF BA_DEF_DEF
#TODO add multiplex-support

from lxml import etree
from canmatrix import *
import codecs

def exportDbc(db, filename):
	f = open(filename,"w")

	#not supported BA_DEF BA_DEF_DEF
	f.write( "VERSION \"created by pkl2dbc\"\n\n")
	f.write("\n")

	#Boardunits
	f.write( "BU_: ")
	id = 1
	nodeList = {};
	for bu in db._BUs._liste:
		f.write(bu._name + " ")
	f.write("\n\n")


	#Botschaften
	for bo in db._bl._liste:
		f.write("BO_ %d " % bo._Id + bo._name + ": %d " % bo._Size + bo._Transmitter + "\n")
		for signal in bo._signals:
			f.write(" SG_ " + signal._name + " : %d|%d@%d%c" % (signal._startbit, signal._signalsize,signal._byteorder, signal._valuetype))
			f.write(" (%g,%g)" % (signal._factor, signal._offset))
			f.write(" [%g,%g]" % (signal._min, signal._max))
			f.write(' "')
			f.write(signal._unit.encode('CP1253'))
#			f.write(signal._unit)
#			print signal._unit
			f.write('" ')
			f.write(','.join(signal._reciever) + "\n")
		f.write("\n")
	f.write("\n")

	#signalbezeichnungen
	for bo in db._bl._liste:
		for signal in bo._signals:
			f.write("CM_ SG_ " + "%d " % bo._Id + signal._name  + ' "' + signal._comment + '";\n') 
	f.write("\n")


	#boardunit-attributes:
	for bu in db._BUs._liste:
		for attrib,val in bu._attributes.items():
			f.write('BA_ "' + attrib + '" BU_ ' + bu._name + ' ' + val  + ';\n')
	f.write("\n")

	#boardunit-attributes:
	for attrib,val in db._attributes.items():
		f.write( 'BA_ "' + attrib + '" ' + val  + ';\n')
	f.write("\n")

	#messages-attributes:
	for bo in db._bl._liste:
		for attrib,val in bo._attributes.items():
			f.write( 'BA_ "' + attrib + '" BO_ %d ' % bo._Id + val  + ';\n')
	f.write("\n")

	#signal-attributes:
	for bo in db._bl._liste:
		for signal in bo._signals:
			for attrib,val in signal._attributes.items():
				f.write( 'BA_ "' + attrib + '" SG_ %d ' % bo._Id + signal._name + ' ' + val  + ';\n')
	f.write("\n")


	#signal-values:
	for bo in db._bl._liste:
		for signal in bo._signals:
			if len(signal._values) > 0:
				f.write('VAL_ %d ' % bo._Id + signal._name)		
				for attrib,val in signal._values.items():
					f.write(' ' + str(attrib) + ' ' + str(val))
				f.write(";\n"); 

