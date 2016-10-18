#!/usr/bin/env python3

from __future__ import print_function
from __future__ import absolute_import


import sys
sys.path.append('..')

import canmatrix.convert
import canmatrix.formats
import copy
import os
import re
import shutil
import subprocess

from canmatrix.log import setup_logger, set_log_level
logger = setup_logger('root')
set_log_level(logger, -1)

export_types = []
import_types = []

for canFormat, features in canmatrix.formats.supportedFormats.items():
    if "dump" in features:
        export_types.append(canmatrix.formats.extensionMapping[canFormat])
    if "load" in features:
        import_types.append(canmatrix.formats.extensionMapping[canFormat])

# for f in os.listdir('../canmatrix'):
#    m = re.match('^export(.*).py$', f)
#    if m is not None and m.group(1) != 'all':
#        export_types.append(m.group(1))
#    m = re.match('^import(.*).py$', f)
#    if m is not None and m.group(1) != 'all' and m.group(1) != 'any':
#        import_types.append(m.group(1))

export_types.sort()
# TODO: support testing of xlsx
# export_types.remove('xlsx')
if "fibex" in export_types:
    export_types.remove('fibex')

import_types.sort()

test_file_base = 'test'
converted_path = 'converted'
try:
    shutil.rmtree(converted_path)
except OSError:
    # it's already not there...
    pass

for i in import_types:
    in_file = test_file_base + '.' + i.lower()
    if not os.path.isfile(in_file):
        print('Skipping conversion from missing file ' + in_file)
    else:
        to = copy.copy(export_types)
        try:
            to.remove(i)
        except ValueError:
            # TODO: support testing of xlsx
            pass
        print('{} -> {}'.format(i, to))

        for t in to:
            out_file = os.path.basename(test_file_base)
            # out_file = os.path.splitext(out_file)[0]
            out_file += '.' + t.lower()
            directory = os.path.join(converted_path, 'from_' + i)
            try:
                os.makedirs(directory)
            except OSError:
                # TODO: be more specific: OSError: [Errno 17] File exists:
                # 'converted/from_arxml'
                pass
            out_file = os.path.join(directory, out_file)
            canmatrix.convert.convert(in_file, out_file)

exit_code = subprocess.call(['diff', '-r', 'reference', 'converted'])

if exit_code:
    # difference found
    message = 'difference found'
else:
    # no difference found
    message = 'no difference'

print('\n\n    Testing completed: {message}'.format(**locals()))
