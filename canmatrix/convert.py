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

from .log import setup_logger, set_log_level
logger = setup_logger('root')
import sys
sys.path.append('..')
import os

def convert(infile, outfileName, **options):
    import canmatrix.exportall as ex
    import canmatrix.importall as im
    dbs = {}
    logger.info("Importing " + infile + " ... ")
    if infile[-3:] == 'dbc':
        dbs[""] = im.importDbc(infile, **options)
    elif infile[-3:] == 'dbf':
        dbs[""] = im.importDbf(infile, **options)
    elif infile[-3:] == 'sym':
        dbs[""] = im.importSym(infile, **options)
    elif infile[-3:] == 'kcd':
        dbs[""] = im.importKcd(infile)
    elif infile[-3:] == 'xls':
        dbs[""] = im.importXls(infile, **options)
    elif infile[-4:] == 'xlsx' :
        dbs[""] = im.importXlsx(infile, **options)
    elif infile[-5:] == 'arxml':
        dbs = im.importArxml(infile, **options)
    elif infile[-4:] == 'yaml':
        dbs[""] = im.importYaml(infile)
    else:
        logger.error('\nFile not recognized: ' + infile + "\n")
    logger.info("done\n")


    logger.info("Exporting " + outfileName + " ... ")

    for name in dbs:
        db = dbs[name]

        if 'deleteZeroSignals' in options and options['deleteZeroSignals']:
            db.deleteZeroSignals()
        
        logger.info(name)
        logger.info("%d Frames found" % (db._fl._list.__len__()))

        if len(name) > 0:
            path = os.path.split(outfileName)
            outfile = os.path.join(path[0], name + "_" + path[1])
        else:
            outfile = outfileName
           
        # Get output file extension   
        fileext = '' 
        if 'force_output' in options and options['force_output']:
            # Provided by the command line
            fileext = options['force_output']
        else:
            # Get extension from output filename
            fileext = os.path.splitext(outfile)[1]
       
        # Strip leading '.' from extension, of exists
        fileext = fileext[1:] if fileext.startswith('.') else fileext
         
                        
        if fileext == 'dbc':
            ex.exportDbc(db, outfile, **options)
        elif fileext == 'dbf':
            ex.exportDbf(db, outfile, **options)
        elif fileext == 'sym':
            ex.exportSym(db, outfile, **options)
        elif fileext == 'kcd':
            ex.exportKcd(db, outfile)
        elif fileext == 'xlsx':
            ex.exportXlsx(db, outfile, **options)
        elif fileext == 'xls':
            ex.exportXls(db, outfile, **options)
        elif fileext == 'json':
            ex.exportJson(db, outfile)
        elif fileext == 'arxml':
            ex.exportArxml(db, outfile)
        elif fileext == 'yaml':
            ex.exportYaml(db, outfile)
        elif fileext == 'csv':
            ex.exportCsv(db, outfile)
        else:
            logger.error('File not recognized: ' + outfileName + "\n")
    logger.info("done")

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

    parser.add_option("-v", dest="verbosity", action="count", help="Output verbosity", default=0)
    parser.add_option("-s", dest="silent", action="store_true", help="don't print status messages to stdout. (only errors)", default=False)
    parser.add_option("-f", dest="force_output", help="enforce output format, ignoring output file extension (e.g., -f csv")
    parser.add_option("", "--deleteZeroSignals", action="store_true",
                                      dest="deleteZeroSignals", default=False,
                                     help="delete zero length signals (signals with 0 bit length) from matrix\ndefault False")
    parser.add_option("", "--arxmlIgnoreClusterInfo", action="store_true",
                                      dest="arxmlIgnoreClusterInfo", default=False,
                                     help="Ignore any can cluster info from arxml; Import all frames in one matrix\ndefault 0")
    parser.add_option("", "--dbcImportEncoding",
                                      dest="dbcImportEncoding", default="iso-8859-1",
                                      help="Import charset of dbc (relevant for units), maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--dbcImportCommentEncoding",
                                      dest="dbcImportCommentEncoding", default="iso-8859-1",
                                      help="Import charset of Comments in dbc\ndefault iso-8859-1")
    parser.add_option("", "--dbcExportEncoding",
                                      dest="dbcExportEncoding", default="iso-8859-1",
                                      help="Export charset of dbc (relevant for units), maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--dbcExportCommentEncoding",
                                      dest="dbcExportCommentEncoding", default="iso-8859-1",
                                      help="Export charset of comments in dbc\ndefault iso-8859-1")
    parser.add_option("", "--dbfImportEncoding",
                                      dest="dbfImportEncoding", default="iso-8859-1",
                                      help="Import charset of dbf, maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--dbfExportEncoding",
                                      dest="dbfExportEncoding", default="iso-8859-1",
                                      help="Export charset of dbf, maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--symImportEncoding",
                                      dest="symImportEncoding", default="iso-8859-1",
                                      help="Import charset of sym format, maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--symExportEncoding",
                                      dest="symExportEncoding", default="iso-8859-1",
                                      help="Export charset of sym format, maybe utf-8\ndefault iso-8859-1")
    parser.add_option("", "--xlsMotorolaBitFormat",
                                      dest="xlsMotorolaBitFormat", default="msbreverse",
                                      help="Excel format for startbit of motorola codescharset signals\nValid values: msb, lsb, msbreverse\n default msbreverse")

    (cmdlineOptions, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    infile = args[0]
    outfileName = args[1]

    verbosity = cmdlineOptions.verbosity
    if cmdlineOptions.silent:
        # only print error messages, ignore verbosity flag
        verbosity = -1
 
    set_log_level(logger, verbosity)
   
    convert(infile, outfileName, **cmdlineOptions.__dict__)

if __name__ == '__main__':
    sys.exit(main())
