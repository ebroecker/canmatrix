#!/usr/bin/env python3

import canmatrix.exportall as ex
from canmatrix.join import join_frame_by_signal_startbit

files = ["../test/db_B.dbc", "../test/db_A.dbc"]

target = join_frame_by_signal_startbit(files)

#
# export the new (target)-Matrix for example as .dbc:
#
ex.exportDbc(target, "target.dbc")
ex.exportXlsx(target, "target.xlsx")
