#!/usr/bin/env python
import library.exportall as ex
import library.importall as im
import library.canmatrix as cm
import sys

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

if len(sys.argv) < 3:
    sys.stderr.write('Usage: sys.argv[0] import-file export-file\n')
    sys.stderr.write('import-file: *.dbc|*.dbf|*.kcd|*.arxml\n')
    sys.stderr.write('export-file: *.dbc|*.dbf|*.kcd\n')
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

print "Importing " + infile + " ... "
if infile[-3:] == 'dbc':
	db = im.importDbc(infile)
elif infile[-3:] == 'dbf':
	db = im.importDbf(infile)
elif infile[-3:] == 'kcd':
	db = im.importKcd(infile)
elif infile[-3:] == 'xls' or infile[-4:] == 'xlsx' :
	db = im.importXls(infile)
elif infile[-5:] == 'arxml':
	db = im.importArxml(infile)
else:
    sys.stderr.write('\nFile not recognized: ' + infile + "\n")
print "done\n"

print "Exporting " + outfile + " ... "

if outfile[-3:] == 'dbc':
	db = ex.exportDbc(db, outfile)
elif outfile[-3:] == 'dbf':
	db = ex.exportDbf(db, outfile)
elif outfile[-3:] == 'kcd':
	db = ex.exportKcd(db, outfile)
else:
    sys.stderr.write('File not recognized: ' + infile + "\n")
print "done"
