#!/usr/bin/env python3
import canmatrix.formats
import sys
cluster = canmatrix.formats.loadp(sys.argv[1], decode_flexray = True)

for cm in cluster:
    for frame in cluster[cm]:
        frame_info = "{}-{}-{}".format(frame.slot_id, frame.base_cycle, frame.repitition_cycle)
        for pdu in frame.pdus:
            for signal in pdu.signals:
                sig_group = pdu.get_signal_group_for_signal(signal)
                sig_group = "None" if sig_group is None else sig_group.name
                print("{}: {}, {}, {}, {}, {}".format(frame_info, frame.size, pdu.pdu_type, pdu.name, sig_group, signal.name))

