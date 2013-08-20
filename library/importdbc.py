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
# this script imports dbc-files to a canmatrix-object
# dbc-files are the can-matrix-definitions of canoe
#
#TODO support for: VERSION, NS, BS_, SIG_VALTYPE_, BA_DEF_REL == BA_DEF_??, BA_DEF_DEF_REL_ = BA_DEF_DEF_  ??

from canmatrix import *
import re
import codecs


def importDbc(filename):
####
#CP1253 or iso-8859-1 ???
	dbcImportEncoding = 'iso-8859-1'
	i = 0	
	class FollowUps:
		nothing, signalComment, frameComment, boardUnitComment, globalComment = range(5)
	followUp = FollowUps.nothing
	comment = ""
	signal = None
	frame = None
	boardUnit = None
	db = CanMatrix()
	f = open(filename)
	for line in f:
		i = i+1
		l = line.strip()
		if l.__len__() == 0:
			continue
		if followUp == FollowUps.signalComment:
			comment += "\n" + l.decode(dbcImportEncoding).replace('\\"','"')
			if l.endswith('";'):
				followUp = FollowUps.nothing
				if signal is not None:
					signal.addComment(comment[0:-2])
			continue;
		elif followUp == FollowUps.frameComment:
			comment += "\n" + l.decode(dbcImportEncoding).replace('\\"','"')
			if l.endswith('";'):
				followUp = FollowUps.nothing
				if frame is not None:
					frame.addComment(comment[0:-2])
			continue;
		elif followUp == FollowUps.boardUnitComment:
			comment += "\n" + l.decode(dbcImportEncoding).replace('\\"','"')
			if l.endswith('";'):
				followUp = FollowUps.nothing
				if boardUnit is not None:
					boardUnit.addComment(comment[0:-2])
			continue;	
		if l.startswith("BO_ "):
			regexp = re.compile("^BO\_ (\w+) (\w+) *: (\w+) (\w+)")		
			temp = regexp.match(l)
			db._fl.addFrame(Frame(temp.group(1), temp.group(2), temp.group(3), temp.group(4)))
		elif l.startswith("SG_ "):
			regexp = re.compile("^SG\_ (\w+) : (\d+)\|(\d+)@(\d+)([\+|\-]) \(([0-9.+\-eE]+),([0-9.+\-eE]+)\) \[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] \"(.*)\" (.*)")		
			temp = regexp.match(l)
			if temp:
				reciever = map(str.strip, temp.group(11).split(',')) 
				db._fl.addSignalToLastFrame(Signal(temp.group(1), temp.group(2), temp.group(3), temp.group(4), temp.group(5), temp.group(6), temp.group(7),temp.group(8),temp.group(9),temp.group(10).decode(dbcImportEncoding),reciever))
			else:
				regexp = re.compile("^SG\_ (\w+) (\w+) *: (\d+)\|(\d+)@(\d+)([\+|\-]) \(([0-9.+\-eE]+),([0-9.+\-eE]+)\) \[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] \"(.*)\" (.*)")
				temp = regexp.match(l)
				reciever = map(str.strip, temp.group(12).split(','))
				multiplex = temp.group(2)
				if multiplex == 'M':
					multiplex = 'Multiplexor'
				else:
					multiplex = int(multiplex[1:])

				db._fl.addSignalToLastFrame(Signal(temp.group(1), temp.group(3), temp.group(4), temp.group(5), temp.group(6), temp.group(7),temp.group(8),temp.group(9),temp.group(10),temp.group(11).decode(dbcImportEncoding),reciever, multiplex))


		elif l.startswith("BO_TX_BU_ "):
			regexp = re.compile("^BO_TX_BU_ ([0-9]+) *: *(.+);")
			temp = regexp.match(l)
			botschaft = db.frameById(temp.group(1))
			for bu in temp.group(2).split(','):
				botschaft.addTransmitter(bu)
		elif l.startswith("CM_ SG_ "):
			regexp = re.compile("^CM\_ SG\_ *(\w+) *(\w+) *\"(.*)\";")		
			temp = regexp.match(l)
			if temp:
				botschaft = db.frameById(temp.group(1))
				signal = botschaft.signalByName(temp.group(2))
				if signal:
					signal.addComment(temp.group(3).decode(dbcImportEncoding).replace('\\"','"'))
			else:
				regexp = re.compile("^CM\_ SG\_ *(\w+) *(\w+) *\"(.*)")		
				temp = regexp.match(l)
				if temp:
					botschaft = db.frameById(temp.group(1))
					signal = botschaft.signalByName(temp.group(2))
					comment = temp.group(3).decode(dbcImportEncoding).replace('\\"','"')
					followUp = FollowUps.signalComment
					
		elif l.startswith("CM_ BO_ "):
			regexp = re.compile("^CM\_ BO\_ *(\w+) *\"(.*)\";")		
			temp = regexp.match(l)
			if temp:
				frame = db.frameById(temp.group(1))
				if frame:
					frame.addComment(temp.group(2).decode(dbcImportEncoding).replace('\\"','"'))
			else:
				regexp = re.compile("^CM\_ BO\_ *(\w+) *\"(.*)")		
				temp = regexp.match(l)
				if temp:
					frame = db.frameById(temp.group(1))
					comment = temp.group(2).decode(dbcImportEncoding).replace('\\"','"')
					followUp = FollowUps.frameComment
		elif l.startswith("CM_ BU_ "):
			regexp = re.compile("^CM\_ BU\_ *(\w+) *\"(.*)\";")		
			temp = regexp.match(l)
			if temp:
				boardUnit = db.boardUnitByName(temp.group(1))
				if boardUnit:
					boardUnit.addComment(temp.group(2).decode(dbcImportEncoding).replace('\\"','"'))
			else:
				regexp = re.compile("^CM\_ BU\_ *(\w+) *\"(.*)")		
				temp = regexp.match(l)
				if temp:
					boardUnit = db.boardUnitByName(temp.group(1))
					if boardUnit:
						comment = temp.group(2).decode(dbcImportEncoding).replace('\\"','"')
						followUp = FollowUps.boardUnitComment
		elif l.startswith("BU_:"):
			regexp = re.compile("^BU\_\:(.*)")		
			temp = regexp.match(l)
			if temp:
				myTempListe = temp.group(1).split(' ')
				for ele in myTempListe:
					if len(ele.strip()) > 1:			
						db._BUs.add(BoardUnit(ele))

		elif l.startswith("VAL_ "):
			regexp = re.compile("^VAL\_ (\w+) (\w+) (.*);")		
			temp = regexp.match(l)
			if temp:
				botschaftId = temp.group(1)
				signal = temp.group(2) 
				tempList = temp.group(3).split('"')
				try:
					for i in range(len(tempList)/2):
						bo = db.frameById(botschaftId)
						sg = bo.signalByName(signal)
						val = tempList[i*2+1]
						#[1:-1]
						
						if sg:
							sg.addValues(tempList[i*2], val.decode(dbcImportEncoding))
				except:
					print "Error with Line: ",tempList

		elif l.startswith("VAL_TABLE_ "):
			regexp = re.compile("^VAL\_TABLE\_ (\w+) (.*);")		
			temp = regexp.match(l)
			if temp:
				tableName = temp.group(1)
				tempList = temp.group(2).split('"')
				try:
					valHash = {}
					for i in range(len(tempList)/2):
						val = tempList[i*2+1]
						valHash[tempList[i*2].strip()] = val.strip()
				except:
					print "Error with Line: ",tempList
				db.addValueTable(tableName, valHash)
			else:
				print l

		elif l.startswith("BA_DEF_ SG_ "):
			regexp = re.compile("^BA\_DEF\_ SG\_ +\"([A-Za-z0-9\-_]+)\" +(.+);")		
			temp = regexp.match(l)
			if temp:
				db.addSignalDefines(temp.group(1), temp.group(2).decode(dbcImportEncoding))
		elif l.startswith("BA_DEF_ BO_ "):
			regexp = re.compile("^BA\_DEF\_ BO\_ +\"([A-Za-z0-9\-_]+)\" +(.+);")		
			temp = regexp.match(l)
			if temp:
				db.addFrameDefines(temp.group(1), temp.group(2).decode(dbcImportEncoding))
		elif l.startswith("BA_DEF_ BU_ "):
			regexp = re.compile("^BA\_DEF\_ BU\_ +\"([A-Za-z0-9\-_]+)\" +(.+);")		
			temp = regexp.match(l)
			if temp:
				db.addBUDefines(temp.group(1), temp.group(2).decode(dbcImportEncoding))
		elif l.startswith("BA_DEF_ "):
			regexp = re.compile("^BA\_DEF\_ +\"([A-Za-z0-9\-_]+)\" +(.+);")		
			temp = regexp.match(l)
			if temp:
				db.addGlobalDefines(temp.group(1), temp.group(2).decode(dbcImportEncoding))

		elif l.startswith("BA_ "):
			regexp = re.compile("^BA\_ +\"[A-Za-z0-9\-_]+\" +(.+)")		
			tempba = regexp.match(l)
			
			if tempba.group(1).strip().startswith("BO_ "):
				regexp = re.compile("^BA\_ \"(.*)\" BO\_ (\w+) (.+);")		
				temp = regexp.match(l)	
				db.frameById(int(temp.group(2))).addAttribute(temp.group(1),temp.group(3))
			elif tempba.group(1).strip().startswith("SG_ "):
				regexp = re.compile("^BA\_ \"(.*)\" SG\_ (\w+) (\w+) (.+);")		
				temp = regexp.match(l)	
				db.frameById(int(temp.group(2))).signalByName(temp.group(3)).addAttribute(temp.group(1),temp.group(4))
			elif tempba.group(1).strip().startswith("BU_ "):
				regexp = re.compile("^BA\_ \"(.*)\" BU\_ (\w+) (.+);")		
				temp = regexp.match(l)
				db._BUs.byName(temp.group(2)).addAttribute(temp.group(1), temp.group(3))
			else:
				regexp = re.compile("^BA\_ \"([A-Za-z0-9\-\_]+)\" +([\"A-Za-z0-9\-\_]+);")		
				temp = regexp.match(l)
				if temp:
					db.addAttribute(temp.group(1),temp.group(2))


		elif l.startswith("SIG_GROUP_ "):
			regexp = re.compile("^SIG\_GROUP\_ +(\w+) +(\w+) +(\w+) +\:(.*);")		
			temp = regexp.match(l)
			frame = db.frameById(temp.group(1))
			if frame is not None:
				signalArray = temp.group(4).split(' ')
				frame.addSignalGroup(temp.group(2), temp.group(3), signalArray)
		elif l.startswith("BA_DEF_DEF_ "):
			regexp = re.compile("^BA\_DEF\_DEF\_ +\"([A-Za-z0-9\-_]+)\" +(.+)\;")		
			temp = regexp.match(l)
			if temp:
				db.addDefineDefault(temp.group(1), temp.group(2).decode(dbcImportEncoding))
#		else:
#			print "Unrecocniced line: " + l + " (%d) " % i 
	return db



