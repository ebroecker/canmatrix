import canmatrix.formats

my_matrix = canmatrix.formats.loadp_flat(r"C:\Users\edu\Downloads\obd2-test\CSS-Electronics-OBD2-incl-extended-v2.0.dbc")

for num, frame in enumerate(my_matrix.frames):
    print(f"Frame {num}: {frame}")
    print(f" is j1939: {frame.is_j1939}")
    print(f" id:  {frame.arbitration_id}")
    print(f' Format: {frame.attributes["VFrameFormat"]}')
    if frame.is_j1939:
        print(f" pgn: {hex(frame.arbitration_id.pgn)}")
