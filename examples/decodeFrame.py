#!/usr/bin/env python3

import canmatrix.formats
import sys

# command line options...
usage = """
%prog [options]  matrix  frame

matrixX can be any of *.dbc|*.dbf|*.kcd|*.arxml
frame is AAA#YYYYYYYYYYYYYYYY or
       BBBBB#YYYYYYYYYYYYYYYY or


where AAA is standard ID and BBBBB is extended ID

"""

if len(sys.argv) < 3:
    print(usage)
    sys.exit(1)

# load matrix
db = canmatrix.formats.loadp(sys.argv[1], flat_import=True)

# load frame data from argv
frame_string = sys.argv[2]
(arbitration_id_string, hexdata) = frame_string.split('#')

# set arbitration_id
arbitration_id = canmatrix.ArbitrationId(int(arbitration_id_string, 16))
arbitration_id.id = int(arbitration_id_string, 16)

# extended frame?
if len(arbitration_id_string) == 3:
    arbitration_id.extended = False
else:
    arbitration_id.extended = True

# find frame to given arbitration_id
frame = db.frame_by_id(arbitration_id)
can_data = bytearray([int(hexdata[index: index+2],16) for index in range(0,len(hexdata),2)])

# decode frame
decoded = frame.decode(can_data)

#print decoded signals
for (signal, value) in decoded.items():
    print (signal + "\t" + hex(value.raw_value) + "\t(" + str(value.phys_value)+ ")")


