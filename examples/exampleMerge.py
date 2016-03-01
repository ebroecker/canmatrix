#!/usr/bin/env python3

import sys
sys.path.append('..')

# importany loads all import filter
from canmatrix.copy import *
import canmatrix.importany as im
import canmatrix.exportall as ex
#fuer Fileio:
import sys

#
# read source Can-Matrixes
#

# import of one CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db1 = next(iter(im.importany("first.dbc").values()))
# import of a second CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db2 = next(iter(im.importany("second.dbc").values()))

#
# create target Matrix
#

db3 = CanMatrix()

#
# Here a new Can-Matrix can be  'programmed':
# -----------------------------------------------------
#

#Copy Can-ID 1234 from second CAN-Matrix to target-Matrix
copyFrame(1234, db2, db3)

#Copy frame "Engine_123" from first CAN-Matrix to target-Matrix
copyFrame("Engine_123", db1, db3)

#Copy ECU (with all Frames) "Gateway" from first CAN-Matrix to target-Matrix
copyBUwithFrames("Gateway", db1, db3)

#
# -----------------------------------------------------
#


#
#
# export the new (target)-Matrix for example as .dbc:
#

ex.exportDbc(db3, "target.dbc")
