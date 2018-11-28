#!/usr/bin/env python3

import sys
sys.path.append('..')

# importany loads all import filter
import canmatrix
import canmatrix.copy
import canmatrix.formats
# fuer Fileio:
import sys

#
# read source Can-Matrixes
#

# import of one CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db1 = canmatrix.formats.loadp("first.dbc", flatImport=True)
# import of a second CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db2 = canmatrix.formats.loadp("second.dbc", flatImport=True)

#
# create target Matrix
#

db3 = canmatrix.CanMatrix()

#
# Here a new Can-Matrix can be  'programmed':
# -----------------------------------------------------
#

# Copy Can-ID 1234 from second CAN-Matrix to target-Matrix
canmatrix.copy.copyFrame(1234, db2, db3)

# Copy frame "Engine_123" from first CAN-Matrix to target-Matrix
canmatrix.copy.copyFrame("Engine_123", db1, db3)

# Copy ECU (with all Frames) "Gateway" from first CAN-Matrix to target-Matrix
canmatrix.copy.copyBUwithFrames("Gateway", db1, db3)

#
# -----------------------------------------------------
#


#
#
# export the new (target)-Matrix for example as .dbc:
#

canmatrix.formats.dumpp(db3, "target.dbc")
