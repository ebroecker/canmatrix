#!/usr/bin/env python3
import canmatrix.formats
import can.io.player
import time

start = time.time()

reader = can.io.player.LogReader("OBD2.asc")
db = canmatrix.formats.loadp_flat("obd2.dbc")
for logged_frame in reader:
    frame_id = canmatrix.ArbitrationId(logged_frame.arbitration_id)
    frame_data = logged_frame.data
    decoded = db.decode(frame_id, frame_data)
    print(decoded)
end = time.time()

print(end-start)
#    for name, value in decoded.items():
#        print (name, value.named_value)
#        if name == "ParameterID_Service01":
#            if value.phys_value not in value.signal.values:
#                print("ParameterID %d not found" % value.phys_value)
#print("--------------------")