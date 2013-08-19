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
# this script exports xls-files from a canmatrix-object
# xls-files are the can-matrix-definitions displayed in Excel
# TODO: Support Signals with scale-infos and valuetables

import xlwt
import sys
from canmatrix import *

sty_up    = xlwt.easyxf('font: name Arial Narrow; align: rota 90, vertical center, horizontal center','pattern: pattern solid, fore-colour rose') 
sty_norm    = xlwt.easyxf('font: name Arial Narrow, colour black')
sty_first_frame    = xlwt.easyxf('font: name Arial Narrow, colour black; borders: top thin')
sty_white    = xlwt.easyxf('font: name Arial Narrow, colour white') 

# Matrix-Styles
sty_blue = xlwt.easyxf('pattern: pattern solid, fore-colour light_green') 
sty_sender = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25') 
sty_sender_blue = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25, back-colour light_green') 
sty_blue_first_frame = xlwt.easyxf('pattern: pattern solid, fore-colour light_green; borders: top thin') 
sty_sender_first_frame = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25; borders: top thin') 
sty_sender_blue_first_frame = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25, back-colour light_green; borders: top thin') 

def writeFrame(bo, worksheet, row, mystyle):
	worksheet.write(row, 0, label = "%3Xh" % bo._Id, style=mystyle)
	worksheet.write(row, 1, label = bo._name, style=mystyle)
	if "GenMsgCycleTime" in bo._attributes:
		worksheet.write(row, 2, label = int(bo._attributes["GenMsgCycleTime"]) , style=mystyle)
	else:
		worksheet.write(row, 2, label = "", style=mystyle)			
		
	if "GenMsgSendType" in bo._attributes:
		if bo._attributes["GenMsgSendType"] == "5":
			worksheet.write(row, 3, label = "Cyclic+Change" , style=mystyle)
			if "GenMsgDelayTime" in bo._attributes:
				worksheet.write(row, 4, label = int(bo._attributes["GenMsgDelayTime"]) , style=mystyle)
			else:
				worksheet.write(row, 4, label = "", style=mystyle)
		elif bo._attributes["GenMsgSendType"] == "0":
			worksheet.write(row, 3, label = "Cyclic" , style=mystyle)
			worksheet.write(row, 4, label = "", style=mystyle)			
		elif bo._attributes["GenMsgSendType"] == "2":
			worksheet.write(row, 3, label = "BAF" , style=mystyle)
			if "GenMsgNrOfRepetitions" in bo._attributes:		
				worksheet.write(row, 4, label = int(bo._attributes["GenMsgNrOfRepetitions"]) , style=mystyle)
			else:
				worksheet.write(row, 4, label = "", style=mystyle)			
		elif bo._attributes["GenMsgSendType"] == "8":
			worksheet.write(row, 3, label = "DualCycle" , style=mystyle)
			if "GenMsgCycleTimeActive" in bo._attributes:		
				worksheet.write(row, 4, label = int(bo._attributes["GenMsgCycleTimeActive"]) , style=mystyle)
			else:
				worksheet.write(row, 4, label = "", style=mystyle)			
		elif bo._attributes["GenMsgSendType"] == "10":
			worksheet.write(row, 3, label = "None" , style=mystyle)
			if "GenMsgDelayTime" in bo._attributes:
				worksheet.write(row, 4, label = int(bo._attributes["GenMsgDelayTime"]) , style=mystyle)		
			else:
				worksheet.write(row, 4, label = "", style=mystyle)			
		elif bo._attributes["GenMsgSendType"] == "9":
			worksheet.write(row, 3, label = "OnChange" , style=mystyle)
			if "GenMsgNrOfRepetitions" in bo._attributes:		
				worksheet.write(row, 4, label = int(bo._attributes["GenMsgNrOfRepetitions"]) , style=mystyle)		
			else:
				worksheet.write(row, 4, label = "", style=mystyle)			
		elif bo._attributes["GenMsgSendType"] == "1":
			worksheet.write(row, 3, label = "Spontaneous" , style=mystyle)
			if "GenMsgDelayTime" in bo._attributes:
				worksheet.write(row, 4, label = int(bo._attributes["GenMsgDelayTime"]) , style=mystyle)				
			else:
				worksheet.write(row, 4, label = "", style=mystyle)			
		else:
			worksheet.write(row, 3, label = "", style=mystyle)			
			worksheet.write(row, 4, label = "", style=mystyle)			
	else:
		worksheet.write(row, 3, label = "", style=mystyle)			
		worksheet.write(row, 4, label = "", style=mystyle)			


def writeSignal(sig, worksheet, row, mystyle):
	worksheet.write(row, 5, label = (sig._startbit)/8+1, style=mystyle)
	worksheet.write(row, 6, label = (sig._startbit)%8, style=mystyle)
	worksheet.write(row, 7, label = sig._name, style=mystyle)

	if sig._comment is None:
		comment = ""
	else:
		comment = sig._comment
	if sig._multiplex == 'Multiplexor':
		comment = "Mode Signal: " + comment
	elif sig._multiplex is not None:
		comment = "Mode " + str(sig._multiplex) + ":" + comment

	worksheet.write(row, 8, label = comment, style=mystyle)
	worksheet.write(row, 9, label = sig._signalsize, style=mystyle)

	if "GenSigStartValue" in sig._attributes:
		worksheet.write(row, 10, label = "%Xh" % int(sig._attributes["GenSigStartValue"]), style=mystyle)
	else:
		worksheet.write(row, 10, label = " ", style=mystyle)


	if "GenSigSNA" in sig._attributes:
		sna = sig._attributes["GenSigSNA"][1:-1]
		worksheet.write(row, 11, label = sna, style=mystyle)
	else:
		worksheet.write(row, 11, label = " ", style=mystyle)	

	if sig._byteorder == 1:
		worksheet.write(row, 12, label = "i", style=mystyle)
	else:
		worksheet.write(row, 12, label = "m", style=mystyle)
	
def writeValue(label, value, worksheet, row, col, mystyle):
	worksheet.write(row, col, label = label, style=mystyle)
	worksheet.write(row, col+1, label = value, style=mystyle)

def writeBuMatrix(buList, sig, bo, worksheet, row, col, firstframe = None):
	if firstframe is not None:
		norm = sty_first_frame
		sender = sty_sender_first_frame
		norm_blue = sty_blue_first_frame
		sender_blue = sty_sender_blue_first_frame
	else:
		norm = sty_norm
		sender = sty_sender
		norm_blue = sty_blue
		sender_blue = sty_sender_blue
		
	for bu in buList:
		if col % 2 == 0:
			locStyle = norm
			locStyleSender = sender 
		else: 
			locStyle = norm_blue
			locStyleSender = sender_blue
		
		if bu in sig._reciever and bu in bo._Transmitter:
			worksheet.write(row, col, label = "r/s", style = locStyleSender)
		elif bu in sig._reciever:
			worksheet.write(row, col, label = "r", style = locStyle)
		elif bu in bo._Transmitter:
			worksheet.write(row, col, label = "s", style = locStyleSender)
		else:
			worksheet.write(row, col, label = "", style = locStyle)
		col += 1
	return col

def exportXls(db, filename):
	head_top = ['ID', 'Frame Name', 'Cycle Time [ms]', 'Launch Type', 'Launch Parameter', 'Signal Byte No.', 'Signal Bit No.', 'Signal Name', 'Signal Function', 'Signal Length [Bit]', 'Signal Default', ' Signal Not Available', 'Byteorder']
	head_tail = ['Value',	'Name / Phys. Range', 'Function / Increment Unit']

	font = xlwt.Font()
	font.bold = True
	font.name = "Arial Narrow"
	sty_up.font = font 

	workbook = xlwt.Workbook(encoding = 'utf8')
	worksheet = workbook.add_sheet('K-Matrix')
	col = 0

	for head in head_top:
		worksheet.write(0, col, label = head, style=sty_up)
		worksheet.col(col).width = 1111
		col += 1
	
	worksheet.col(1).width = 5555
	worksheet.col(3).width = 3333
	worksheet.col(7).width = 5555
	worksheet.col(8).width = 7777

	buList = []
	for bu in db._BUs._list:
		worksheet.write(0, col, label = bu._name, style=sty_up)
		worksheet.col(col).width = 1111
		buList.append(bu._name)
		col += 1
		
	head_start = col
		
	for head in head_tail:
		worksheet.write(0, col, label = head, style=sty_up)
		worksheet.col(col).width = 3333
		col += 1
		
	worksheet.col(head_start).width = 1111
	worksheet.col(head_start+1).width = 5555

	boHash = {}
	for bo in db._fl._list:
		boHash[int(bo._Id)] = bo

	row = 1

	# iterate over the frames
	for idx in sorted(boHash.iterkeys()):
		bo = boHash[idx]
		framestyle = sty_first_frame 
		
		sigHash ={}
		for sig in bo._signals:
			sigHash[sig._startbit] = sig
		
		sigstyle = sty_first_frame

		for sig_idx in sorted(sigHash.iterkeys()):
			sig = sigHash[sig_idx]		

			if sigstyle != sty_first_frame:
				sigstyle = sty_norm

			if float(sig._offset) != 0 or float(sig._factor) != 1.0:
				writeFrame(bo, worksheet, row, framestyle)
				writeSignal(sig, worksheet, row, sigstyle)
				col = head_top.__len__()
				if framestyle == sty_first_frame:
					col = writeBuMatrix(buList, sig, bo, worksheet, row, col, 1)
				else:
					col = writeBuMatrix(buList, sig, bo, worksheet, row, col)

				if sig._unit.strip().__len__() > 0:
					worksheet.write(row, col+2, label = "%g" % float(sig._factor) + "  " + sig._unit, style=sigstyle)
				else:
					worksheet.write(row, col+2, label = float(sig._factor), style=sigstyle)

				maxi = max(sig._offset, sig._max)
				if maxi == sig._offset:
					maxi = int(sig._offset) + 2 ^ int(sig._signalsize )					
				worksheet.write(row, col, label = " ", style=sigstyle)
				worksheet.write(row, col+1, label = str("%s..%s" %(sig._offset, maxi)), style=sigstyle)
				
				sigstyle = sty_white
				#, sig._startbit, sig._signalsize, sig._byteorder, float(sig._factor), float(sig._offset)])
				row += 1
				framestyle = sty_white
			elif sig._values.__len__() > 0:
				for val in sorted(sig._values.iterkeys()):
					writeFrame(bo, worksheet, row, framestyle)
					writeSignal(sig, worksheet, row, sigstyle)
					col = head_top.__len__()
					if framestyle == sty_first_frame:
						col = writeBuMatrix(buList, sig, bo, worksheet, row, col, 1)
						writeValue(val,sig._values[val], worksheet, row, col, framestyle)
					else:
						col = writeBuMatrix(buList, sig, bo, worksheet, row, col)
						writeValue(val,sig._values[val], worksheet, row, col, sty_norm)
					if sig._unit.strip().__len__() > 0:
						worksheet.write(row, col+2, label = "%g" % float(sig._factor) + "  " + sig._unit, style=sigstyle)
					else:
						worksheet.write(row, col+2, label = float(sig._factor), style=sigstyle)
					row +=1
					sigstyle = sty_white
					framestyle = sty_white
			else: 
				writeFrame(bo, worksheet, row, framestyle)
				writeSignal(sig, worksheet, row, sigstyle)
				col = head_top.__len__()
				if framestyle == sty_first_frame:
					col = writeBuMatrix(buList, sig, bo, worksheet, row, col,1)
				else:
					col = writeBuMatrix(buList, sig, bo, worksheet, row, col)
				if sig._unit.strip().__len__() > 0:
					worksheet.write(row, col+2, label = "%g" % float(sig._factor) + "  " + sig._unit, style=sigstyle)
				else:
					worksheet.write(row, col+2, label = float(sig._factor), style=sigstyle)

				worksheet.write(row, col, label = " ", style=sigstyle)
				worksheet.write(row, col+1, label = " ", style=sigstyle)
				row +=1
				sigstyle = sty_white
				framestyle = sty_white
#			worksheet.write(row-1, col+2, label = str(sig._factor) + " " + sig._unit)

		signals = []

	worksheet.set_panes_frozen(True) # frozen headings instead of split panes
	worksheet.set_horz_split_pos(1) # in general, freeze after last heading row
	worksheet.set_remove_splits(True)
	workbook.save(filename)
