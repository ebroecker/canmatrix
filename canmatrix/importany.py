#!/usr/bin/env python
from __future__ import absolute_import
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

import logging
logger = logging.getLogger('root')

def importany(infile, **options):
    # import within function to disable warning messages by log level
    from . import importall as im
    if "key" in options:
        key = options["key"]
    else:
        key = ""
    dbs = {}
    if infile[-3:] == 'dbc':
        dbs[key] = im.importDbc(infile, **options)
    elif infile[-3:] == 'dbf':
        dbs[key] = im.importDbf(infile, **options)
    elif infile[-3:] == 'sym':
        dbs[key] = im.importSym(infile, **options)
    elif infile[-3:] == 'kcd':
        dbs[key] = im.importKcd(infile)
    elif infile[-3:] == 'xls':
        dbs[key] = im.importXls(infile, **options)
    elif infile[-4:] == 'xlsx' :
        dbs[key] = im.importXlsx(infile, **options)
    elif infile[-5:] == 'arxml':
        dbs = im.importArxml(infile, **options)
    elif infile[-4:] == 'yaml':
        dbs[key] = im.importYaml(infile)
    elif infile[-4:] == 'json':
        dbs[key] = im.importJson(infile)
    else:
        logger.error('\nFile not recognized: ' + infile + "\n")
    logger.info("done\n")

    return dbs
