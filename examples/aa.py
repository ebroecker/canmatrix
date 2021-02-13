#!/usr/bin/env python3
import canmatrix
import json

cm = canmatrix.formats.loadp("j1939.dbc", flat_import = True)
f = open("/home/edu/ownCloud/j1939/j1939.json", "r")
jsonData = json.load(f)

def find_spn(search_spn):
    for pgn in jsonData:
        for spn in jsonData[pgn]:
            if search_spn == spn:
                return pgn
    

for signal in cm.frame_by_name("VECTOR__INDEPENDENT_SIG_MSG"):
    spn = signal.attributes["SPN"]
    pgn = find_spn(spn)
    frame = cm.frame_by_pgn(int(pgn))
    print (frame.name)
