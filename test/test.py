#!/usr/bin/env python3

from __future__ import print_function
from __future__ import absolute_import

import unittest
import copy
import os
import re
import shutil
import subprocess

import sys
sys.path.append('../src')

import canmatrix.convert
import canmatrix.formats


class MatrixTest(unittest.TestCase):

    def setUp(self):
        self.data_path = os.path.dirname(os.path.realpath(__file__))
        self.converted_path = os.path.join(self.data_path, 'converted')
        self.export_types = []
        self.import_types = []
        for canFormat, features in canmatrix.formats.supportedFormats.items():
            if "dump" in features:
                self.export_types.append(canmatrix.formats.extensionMapping[canFormat])
            if "load" in features:
                self.import_types.append(canmatrix.formats.extensionMapping[canFormat])

    def test_conversions(self):
        if sys.version_info > (3, 2):
            self.assertIsNotNone(shutil.which("diff"), "ERROR: this test needs the tool 'diff' in your path to work")

        from canmatrix.log import setup_logger, set_log_level
        logger = setup_logger('root')
        set_log_level(logger, -1)



        # for f in os.listdir('../canmatrix'):
        #    m = re.match('^export(.*).py$', f)
        #    if m is not None and m.group(1) != 'all':
        #        export_types.append(m.group(1))
        #    m = re.match('^import(.*).py$', f)
        #    if m is not None and m.group(1) != 'all' and m.group(1) != 'any':
        #        import_types.append(m.group(1))

        self.export_types.sort()
        # TODO: support testing of xlsx
        # export_types.remove('xlsx')
        if "fibex" in self.export_types:
            self.export_types.remove('fibex')

        self.import_types.sort()

        test_file_base = 'test'
        try:
            shutil.rmtree(self.converted_path)
        except OSError:
            # it's already not there...
            pass

        for i in self.import_types:
            in_file = os.path.join(self.data_path, test_file_base + '.' + i.lower())
            if not os.path.isfile(in_file):
                print('Skipping conversion from missing file ' + in_file)
            else:
                to = copy.copy(self.export_types)
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
                    directory = os.path.join(self.converted_path, 'from_' + i)
                    try:
                        os.makedirs(directory)
                    except OSError:
                        # TODO: be more specific: OSError: [Errno 17] File exists:
                        # 'converted/from_arxml'
                        pass
                    out_file = os.path.join(directory, out_file)
                    canmatrix.convert.convert(in_file, out_file)

        exit_code = subprocess.call(['diff', '-r', 'reference', 'converted'])
        # self.assertNotEqual(exit_code, 0, "difference found")
        if exit_code:
            # difference found
            message = 'difference found'
        else:
            # no difference found
            message = 'no difference'

        print('\n\n    Testing completed: {message}'.format(**locals()))


if __name__ == "__main__":
    unittest.main()
