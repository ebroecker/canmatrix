#!/usr/bin/env python
from library.canmatrixGenerateJS import *
import library.importany as im
import sys
import string
import os

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
    sys.stderr.write('export-file: somefile.js\n')
    sys.exit(1)

infile = sys.argv[1]
outfile = os.path.splitext(sys.argv[2])[0]

generatorConfig = {
'nice' : 1
}

db = im.importany(infile)

[botschafenFeld, constants, macros, globalMessagesRaw, framedecodeMethods, framedecodeSwitch] = generateCode_js(db,db._bl._liste,generatorConfig)	

dbcFileName = os.path.splitext(infile)[0]

f = open(outfile + ".js", "w")
f.write("var " + dbcFileName + " = { \n")
f.write(botschafenFeld + "\n")
f.write(constants + "\n")
f.write(macros + "\n")
f.write(framedecodeMethods + "\n")
f.write("}\n")
quit()

