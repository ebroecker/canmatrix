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

from canmatrix import *
import codecs

dbcExportEncoding = 'iso-8859-1'
#CP1253

def exportDbc(db, filename):
	f = open(filename,"w")

	f.write( "VERSION \"created by canmatrix\"\n\n")
	f.write("\n")

	f.write("NS_ :\n\nBS_:\n\n")

	
	#Boardunits
	f.write( "BU_: ")
	id = 1
	nodeList = {};
	for bu in db._BUs._list:
		f.write(bu._name + " ")
	f.write("\n\n")

	#ValueTables
	for table in db._valueTables:
		f.write("VAL_TABLE_ " + table )
		for row in db._valueTables[table]:
			f.write(' ' + row + ' "' + db._valueTables[table][row] + '"')
		f.write(";\n")
	f.write("\n")
		
	#Frames
	for bo in db._fl._list:
		if bo._Transmitter.__len__() == 0:
			bo._Transmitter = ["Vector__XXX"]

		if bo._extended == 1:
			bo._Id += 0x80000000
			
		f.write("BO_ %d " % bo._Id + bo._name + ": %d " % bo._Size + bo._Transmitter[0] + "\n")
		for signal in bo._signals:
			f.write(" SG_ " + signal._name)
			if signal._multiplex == 'Multiplexor':
				f.write(' M ')
			elif signal._multiplex is not None:
				f.write(" m%d " % int(signal._multiplex))

			f.write(" : %d|%d@%d%c" % (signal._startbit, signal._signalsize,signal._byteorder, signal._valuetype))
			f.write(" (%s,%s)" % (signal._factor, signal._offset))
			f.write(" [%s|%s]" % (signal._min, signal._max))
			f.write(' "')

			f.write(signal._unit.encode(dbcExportEncoding))
			f.write('" ')
			if signal._reciever.__len__() == 0:
				signal._reciever = ['Vector__XXX']
			f.write(','.join(signal._reciever) + "\n")
		f.write("\n")
	f.write("\n")

	#second Sender:
	for bo in db._fl._list:
		if bo._Transmitter.__len__() > 1:
			f.write("BO_TX_BU_ %d : %s;\n" % (bo._Id,','.join(bo._Transmitter)))

	#frame comments
	for bo in db._fl._list:
		if bo._comment is not None and bo._comment.__len__() > 0:
			f.write("CM_ BO_ " + "%d " % bo._Id + ' "')
			f.write(bo._comment.encode(dbcExportEncoding,'replace').replace('"','\\"'))
			f.write('";\n') 
	f.write("\n")
			
	#signal comments
	for bo in db._fl._list:
		for signal in bo._signals:
			if signal._comment is not None and signal._comment.__len__() > 0:
				f.write("CM_ SG_ " + "%d " % bo._Id + signal._name  + ' "')
				f.write(signal._comment.encode(dbcExportEncoding,'replace').replace('"','\\"'))
				f.write('";\n') 
	f.write("\n")

	#boarUnit comments
	for bu in db._BUs._list:
		if bu._comment is not None and bu._comment.__len__() > 0:
			f.write("CM_ BU_ " + bu._name + ' "' + bu._comment.encode(dbcExportEncoding,'replace').replace('"','\\"') + '";\n') 
	f.write("\n")

	defaults = {}
	for (type,define) in db._frameDefines.items():
		f.write('BA_DEF_ BO_ "' + type + '" ' + define._definition.encode(dbcExportEncoding,'replace') + ';\n')
		if type not in defaults and define._defaultValue is not None:
			defaults[type] = define._defaultValue
	for (type,define) in db._signalDefines.items():
		f.write('BA_DEF_ SG_ "' + type + '" ' + define._definition.encode(dbcExportEncoding,'replace') + ';\n')
		if type not in defaults and define._defaultValue is not None:
			defaults[type] = define._defaultValue
	for (type,define) in db._buDefines.items():
		f.write('BA_DEF_ BU_ "' + type + '" ' + define._definition.encode(dbcExportEncoding,'replace') + ';\n')
		if type not in defaults and define._defaultValue is not None:
			defaults[type] = define._defaultValue
	for (type,define) in db._globalDefines.items():
		f.write('BA_DEF_ "' + type + '" ' + define._definition.encode(dbcExportEncoding,'replace') + ';\n')
		if type not in defaults and define._defaultValue is not None:
			defaults[type] = define._defaultValue

	for define in defaults:
		f.write('BA_DEF_DEF_ "' + define + '" ' + defaults[define].encode(dbcExportEncoding,'replace') + ';\n')

		
	#boardunit-attributes:
	for bu in db._BUs._list:
		for attrib,val in bu._attributes.items():
			f.write('BA_ "' + attrib + '" BU_ ' + bu._name + ' ' + val  + ';\n')
	f.write("\n")

	#global-attributes:
	for attrib,val in db._attributes.items():
		f.write( 'BA_ "' + attrib + '" ' + val  + ';\n')
	f.write("\n")
	
	#messages-attributes:
	for bo in db._fl._list:
		for attrib,val in bo._attributes.items():
			f.write( 'BA_ "' + attrib.encode(dbcExportEncoding) + '" BO_ %d ' % bo._Id + val + ';\n')
	f.write("\n")
			
	#signal-attributes:
	for bo in db._fl._list:
		for signal in bo._signals:
			for attrib,val in signal._attributes.items():
				f.write( 'BA_ "' + attrib + '" SG_ %d ' % bo._Id + signal._name + ' ' + val  + ';\n')
	f.write("\n")

	#signal-values:
	for bo in db._fl._list:
		for signal in bo._signals:
			if len(signal._values) > 0:
				f.write('VAL_ %d ' % bo._Id + signal._name)		
				for attrib,val in signal._values.items():
					f.write(' ' + str(attrib) + ' "' + str(val.encode(dbcExportEncoding)) + '"')
				f.write(";\n"); 


	#signal-groups:
	for bo in db._fl._list:
		for sigGroup in bo._SignalGroups:
			f.write("SIG_GROUP_ " + str(bo._Id) + " " + sigGroup._name + " " + str(sigGroup._Id)+ " :") 
			for signal in sigGroup._members:
				f.write(" " + signal._name)
			f.write(";\n")



