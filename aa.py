import canmatrix.formats

db = canmatrix.formats.loadp_flat("example.dbc")

for signal in db.frames[0].signals:
    print("{} Startbit: {}".format(signal.name, signal.get_startbit(bit_numbering=1)))

