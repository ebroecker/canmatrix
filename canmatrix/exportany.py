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

from __future__ import absolute_import
import os.path
import logging
logger = logging.getLogger('root')


def exportany(db, outfile, **options):
    from . import exportall as ex

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
        ex.exportJson(db, outfile, **options)
    elif fileext == 'arxml':
        ex.exportArxml(db, outfile, **options)
    elif fileext == 'yaml':
        ex.exportYaml(db, outfile)
    elif fileext == 'csv':
        ex.exportCsv(db, outfile)
    elif fileext == 'xml':
        ex.exportFibex(db, outfile)
    else:
        logger.error('File not recognized: ' + outfile + "\n")
