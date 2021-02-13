import canmatrix.formats
j1939_db = canmatrix.formats.loadp_flat("j1939.dbc", dbcImportEncoding="utf8")
for frame in j1939_db.frames:
    frame.is_j1939 = True
canmatrix.formats.dumpp({"":j1939_db},"j1939_a.dbc", dbcExportEncoding="utf8")
