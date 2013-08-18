#!/usr/bin/env python
# importany laed alle verfuegbaren importfilter
from library.copy import *
import library.importany as im
import library.exportall as ex
#fuer Fileio:
import sys

#
# Einlesen der Quell-Matritzen
#

# Importieren einer CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db1 = im.importany("aa.dbc")
# Importieren einer 2. CAN-Matrix (*.dbc, *.dbf, *.kcd, *.arxml)
db2 = im.importany("aa.dbc")

#
# Ziel-Matrix anlegen
#

db3 = CanMatrix()

#
# Hier kann die neue Can-Matrix 'Programmiert' werden:
# -----------------------------------------------------
#

#Kopiere ID 1234 aus der 2. K-Matrix in die Zielmatrix
copyFrame(1234, db2, db3)

#Kopiere Frame "Engine_123" aus der 1. K-Matrix in die Zielmatrix
copyFrame("Engine_123", db1, db3)

#Kopiere ECU "Gateway" aus der 1. K-Matrix (mit allen zugehoerigen Frames) in die Zielmatrix
copyBUwithFrames("Gateway", db1, db3)

#
# -----------------------------------------------------
#


#
#
# Exportieren der neuen matrix z.B. als dbc:
#

ex.exportDbc(db3, "ziel.dbc")
