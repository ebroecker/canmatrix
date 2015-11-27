#!/usr/bin/env python
# importany laed alle verfuegbaren importfilter
from library.copy import *
import library.importany as im
import library.exportall as ex
#fuer Fileio:
import sys

#
# read source Can-Matrixes
#

# import of one CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db1 = im.importany("first.dbc")
# import of a second CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db2 = im.importany("second.dbc")

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
