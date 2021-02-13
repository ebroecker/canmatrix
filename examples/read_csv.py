import canmatrix.j1939_decoder
import csv
import re

can_ids = []
with open("test_DataGroup_1.csv") as f:
    reader = csv.reader(f)
    matrix = canmatrix.formats.loadp_flat("/home/edu/j1939/CSS-Electronics-SAE-J1939-DEMO_CF00400.dbc", dbcImportEncoding="utf8")
    t = canmatrix.j1939_decoder.j1939_decoder()
    for row in reader:
        timestamp = float(row[0])
        can_id =  (int(row[3]))
        can_data = re.split(" +", row[7].replace("[","").replace("]","").strip())
        can_data = [int(a) for a in can_data]

        if can_id not in can_ids:
            can_ids.append(can_id)
            (type, signals) = t.decode(canmatrix.ArbitrationId(id = can_id, extended= True), bytearray(can_data), None)
            if len(signals):
                print (type, signals)
            else:
                print(hex(can_id))
                print(canmatrix.ArbitrationId(id = can_id, extended= True).pgn)

#        can_data = ["%02X" % a for a in can_data]
#        print("%g  %08x#%s" % (timestamp, can_id, "".join(can_data)))
