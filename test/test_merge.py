#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import print_function

import sys

sys.path.append('..')

import shutil

# importany loads all import filter
from canmatrix.copy import *
import canmatrix.importany as im

# fuer Fileio:


test_file_base = 'db_'
converted_path = 'converted'
try:
    shutil.rmtree(converted_path)
except OSError:
    # it's already not there...
    pass

#
# read source Can-Matrixes
#

## import of one CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
# db1 = next(iter(im.importany("db_A.dbc").values()))
## import of a second CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
# db2 = next(iter(im.importany("db_B.dbc").values()))


files = ["db_A.dbc", "db_B.dbc"]

#
# create target Matrix
#
dbres = CanMatrix()

# for frame in db1._fl._list:
#    print(frame._name)

# for frame in db2._fl._list:
#    print(frame._name)

for f in files:
    db = next(iter(im.importany(f).values()))
    print('___________')
    print(f)
    print('--_--_--_--')
    for frame in db._fl._list:
        print(frame._name)

# db1.frameById(self, Id):
#    return self._fl.byId(Id)
# def frameByName(self, name):

#
# Here a new Can-Matrix can be  'programmed':
# -----------------------------------------------------
#

# Copy Can-ID 1234 from second CAN-Matrix to target-Matrix
# copyFrame(1234, db2, db3)

# Copy frame "Engine_123" from first CAN-Matrix to target-Matrix
# copyFrame("Engine_123", db1, db3)

# Copy ECU (with all Frames) "Gateway" from first CAN-Matrix to target-Matrix
# copyBUwithFrames("Gateway", db1, db3)

#
# -----------------------------------------------------
#


#
#
# export the new (target)-Matrix for example as .dbc:
#

# ex.exportDbc(dbres, "target.dbc")
