import canmatrix
dbm = canmatrix.formats.loadp_flat("MRR360_Mod.dbc")
dbs = canmatrix.CanMatrix()

canmatrix.copy.copy_ecu_with_frames("SODFL", dbm, dbs)

canmatrix.formats.dumpp({"":dbs}, "out.dbc")