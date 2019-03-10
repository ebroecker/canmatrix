#!/usr/bin/env python3

import canmatrix.formats
from canmatrix.join import join_frame_by_signal_start_bit

files = ["../test/db_B.dbc", "../test/db_A.dbc"]

target = join_frame_by_signal_start_bit(files)

#
# export the new (target)-Matrix for example as .dbc:
#
canmatrix.formats.dumpp(target, "target.dbc")
canmatrix.formats.dumpp(target, "target.xlsx")
