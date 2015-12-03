#!/usr/bin/env python3

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

from __future__ import print_function
from __future__ import absolute_import

import sys
sys.path.append('..')

import canmatrix.exportall as ex
import canmatrix.importall as im
import canmatrix.canmatrix as cm
import os

def convert(infile, outfileName, dbcCharset='iso-8859-1', dbcCommentCharset='iso-8859-1'):
    dbs = {}
    print("Importing " + infile + " ... ")
    if infile[-3:] == 'dbc':
        dbs[""] = im.importDbc(infile, dbcCharset,  dbcCommentCharset)
    elif infile[-3:] == 'dbf':
        dbs[""] = im.importDbf(infile)
    elif infile[-3:] == 'sym':
        dbs[""] = im.importSym(infile)
    elif infile[-3:] == 'kcd':
        dbs[""] = im.importKcd(infile)
    elif infile[-3:] == 'xls':
        dbs[""] = im.importXls(infile)
    elif infile[-4:] == 'xlsx' :
        dbs[""] = im.importXlsx(infile)
    elif infile[-5:] == 'arxml':
        dbs = im.importArxml(infile)
    elif infile[-4:] == 'yaml':
        dbs[""] = im.importYaml(infile)
    else:
        sys.stderr.write('\nFile not recognized: ' + infile + "\n")
    print("done\n")


    print("Exporting " + outfileName + " ... ")

    for name in dbs:
        db = dbs[name]
        print(name)
        print("%d Frames found" % (db._fl._list.__len__()))

        if len(name) > 0:
            path = os.path.split(outfileName)
            outfile = os.path.join(path[0], name + "_" + path[1])
        else:
            outfile = outfileName
        if outfile[-3:] == 'dbc':
            ex.exportDbc(db, outfile, dbcCharset,  dbcCommentCharset)
        elif outfile[-3:] == 'dbf':
            ex.exportDbf(db, outfile)
        elif outfile[-3:] == 'sym':
            ex.exportSym(db, outfile)
        elif outfile[-3:] == 'kcd':
            ex.exportKcd(db, outfile)
        elif outfile[-4:] == 'xlsx':
            ex.exportXlsx(db, outfile)
        elif outfile[-3:] == 'xls':
            ex.exportXls(db, outfile)
        elif outfile[-4:] == 'json':
            ex.exportJson(db, outfile)
        elif outfile[-5:] == 'arxml':
            ex.exportArxml(db, outfile)
        elif outfile[-4:] == 'yaml':
            ex.exportYaml(db, outfile)
        elif outfile[-3:] == 'csv':
            ex.exportCsv(db, outfile)
        else:
            sys.stderr.write('File not recognized: ' + outfileName + "\n")
    print("done")

def main():
    from optparse import OptionParser

    usage = """
    %prog [options] import-file export-file

    import-file: *.dbc|*.dbf|*.kcd|*.arxml|*.xls(x)|*.sym
    export-file: *.dbc|*.dbf|*.kcd|*.json|*.xls(x)

    """

    parser = OptionParser(usage=usage)
    #parser.add_option("-d", "--debug",
    #                  dest="debug", default=False,
    #                  help="print debug messages to stdout")
    parser.add_option("", "--dbcCharset",
                                      dest="dbcCharset", default="iso-8859-1",
                                      help="Charset of Comments in dbc, maybe utf-8")
    parser.add_option("", "--dbcCommentCharset",
                                      dest="dbcCommentCharset", default="iso-8859-1",
                                      help="Charset of Comments in dbc")
    (cmdlineOptions, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(1)
    infile = args[0]
    outfileName = args[1]

    convert(infile=infile, outfileName=outfileName,
                    dbcCharset=cmdlineOptions.dbcCharset, dbcCommentCharset=cmdlineOptions.dbcCommentCharset)

if __name__ == '__main__':
    sys.exit(main())
