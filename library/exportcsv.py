#!/usr/bin/env python
#Copyright (c) 2013, Eduard Broecker 
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the aframeve copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the aframeve copyright notice, this list of conditions and the
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
# this script exports csv-files from a canmatrix-object
# csv-files are the can-matrix-definitions displayed in Excel
# Author: Martin Hoffmann (hoffmmn) martin.hoffmann2@brose.com

import xlsxwriter
import sys
from canmatrix import *
import os.path

def exportCsv(db, filename):
	head_top = ['ID', 'Frame Name', 'Cycle Time [ms]', 'Launch Type', 'Launch Parameter', 'Signal Byte No.', 'Signal Bit No.', 'Signal Name', 'Signal Function', 'Signal Length [Bit]', 'Signal Default', ' Signal Not Available', 'Byteorder']
	head_tail = ['Value',	'Name / Phys. Range', 'Function / Increment Unit']

	# TODO: Prepare csv file
# 	workbook = xlsxwriter.Workbook(filename)
# 	wsname = os.path.basename(filename).replace('.xlsx','')
# 	worksheet = workbook.add_worksheet('K-Matrix ' + wsname[0:22])
	col = 0


	# write first row (header) cols before frameardunits:
 	for head in head_top:
		#worksheet.write(0, col, head, sty_header)
		#worksheet.set_column(col, col, 3.57)
# 		print head + ","
 		col += 1

	# Print head and tail...
	print "-- headers: Must be merged to a single line..."
	print ",".join(head_top)

	# write frameardunits in first row:
 	buList = []
 	for bu in db._BUs._list:
		#worksheet.write(0, col, bu._name, sty_header)
		#worksheet.set_column(col, col, 3.57)
 		buList.append(bu._name)
 		col += 1
 		
	print ",".join([bu._name for bu in db._BUs._list])

	head_start = col
		
	# write first row (header) cols after frameardunits:
 	for head in head_tail:
# 		worksheet.write(0, col,  head, sty_header)
# 		worksheet.set_column(col, col, 6)
 		col += 1

 	print ",".join(head_tail)
	print "-- headers end..."

	frameHash = {}
	for frame in db._fl._list:
		frameHash[int(frame._Id)] = frame
	
	#set row to first Frame (row = 0 is header)
	row = 1
	
	
	# iterate over the frames
	for idx in sorted(frameHash.iterkeys()):
		frame = frameHash[idx]
		
		#sort signals:
		sigHash ={}
		for sig in frame._signals:
			sigHash["%02d" % int(sig._startbit) + sig._name] = sig
		
		#iterate over signals
		for sig_idx in sorted(sigHash.iterkeys()):
			sig = sigHash[sig_idx]		

			# valuetable available?
			if sig._values.__len__() > 0:
				# iterate over values in valuetable
				for val in sorted(sig._values.iterkeys()):
# 					writeFramex(frame, worksheet, row, framestyle)
					col = head_top.__len__()
# 					col = writeBuMatrixx(buList, sig, frame, worksheet, row, col, framestyle)
					# write Value
# 					writeValuex(val,sig._values[val], worksheet, row, col, valstyle)					
# 					writeSignalx(db, sig, worksheet, row, col, sigstyle)

					# no min/max here, because min/max has same col as values...
					#next row					
					row +=1
				#loop over values ends here
			# no valuetable available
			else: 
# 				writeFramex(frame, worksheet, row, framestyle)
				col = head_top.__len__()
# 				col = writeBuMatrixx(buList, sig, frame, worksheet, row, col, framestyle)		
# 				writeSignalx(db, sig, worksheet, row, col, sigstyle)	
			
# 				if float(sig._min) != 0 or float(sig._max) != 1.0:
# # 					worksheet.write(row, col+1, str("%s..%s" %(sig._min, sig._max)), sigstyle)
# 				else:
# 					worksheet.write(row, col+1,  "", sigstyle)

				#next row					
				row +=1
				# set style to normal - without border
		# reset signal-Array
		signals = []
		#loop over signals ends here
	# loop over frames ends here
		
	# save file
