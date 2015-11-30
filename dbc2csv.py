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

from library.exportcsv import *
import library.importdbc as imdbc
import library.importdbf as imdbf
import library.canmatrix as cm
import sys
from optparse import OptionParser

usage = """
%prog [options] import-file [export-file]

import-file: *.dbc|*.dbf
export-file: *.csv

"""

parser = OptionParser(usage=usage)
parser.add_option("-d", "--delimiter", 
                  dest="delimiter", default=",",
                  help="csv delimiter")
parser.add_option("", "--dbcCharset", 
                  dest="dbcCharset", default="iso-8859-1",
                  help="Charset of Comments in dbc, maybe utf-8")
parser.add_option("", "--dbcCommentCharset", 
                  dest="dbcCommentCharset", default="iso-8859-1",
                  help="Charset of Comments in dbc")
(cmdlineOptions, args) = parser.parse_args()


if len(args) < 1:
    parser.print_help()
    sys.exit(1)

dbs = {}
if len(args) > 0:
    infile = args[0]
    
outfile = None
if len(args) > 1:
    outfile = args[1]

# print "Importing " + infile + " ... "
if infile[-3:] == 'dbc':
	dbs[""] = imdbc.importDbc(infile, cmdlineOptions.dbcCharset,  cmdlineOptions.dbcCommentCharset)
elif infile[-3:] == 'dbf':
	dbs[""] = imdbf.importDbf(infile)
else:
    sys.stderr.write('\nFile not recognized: ' + infile + "\n")

# print "Exporting " + outfileName + " ... "

for name in dbs:
	db = dbs[name]
# 	print "%d Frames found" % (db._fl._list.__len__())
	
	if len(name) > 0:
        	outfile = name + "_" + outfile
	else:
		outfile = outfile

	exportCsv(db, outfile, cmdlineOptions.delimiter)
