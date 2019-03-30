#!/usr/bin/env python3

import canmatrix.formats
import sys
import optparse

# command line options...
usage = """
%prog [options]  matrix

matrixX can be any of *.dbc|*.dbf|*.kcd|*.arxml
"""

parser = optparse.OptionParser(usage=usage)
parser.add_option(
    "-f", "--frames",
    dest="frames",
    help="encode list of frames",
    default="*")

(cmdlineOptions, args) = parser.parse_args()

if len(args) < 1:
    parser.print_help()
    sys.exit(1)

# load matrix
db = canmatrix.formats.loadp_flat(args[0])

#get all frames which match the commandline
frames = db.glob_frames(cmdlineOptions.frames)

#helper to read physical value from user
def read_signal_value_from_user(signal):
    a = input("Enter Value for " + signal.name + " ")

    if signal.is_float:
        return float(a)
    else:
        return int(a)

# go through all frames
for frame in frames:
    print (frame.name)

    if frame.is_complex_multiplexed:
        # ignore complex multiplexed signals
        continue
    if frame.is_multiplexed:
        # if multiplexed frame search for multiplexer
        multiplexer_signal = frame.get_multiplexer

        # read multiplexer value
        a = input("Enter Value for Multiplexer " + multiplexer_signal.name + " ")
        signalDict = dict()
        signalDict[multiplexer_signal.name] = int(a)

        # read signals for the given multiplexer value
        for signal in frame.get_signals_for_multiplexer_value(int(a)):
            signalDict[signal.name] = read_signal_value_from_user(signal)

    else:
        # not multiplexed frame
        signalDict = dict()
        # go through all signals
        for signal in frame.signals:
            signalDict[signal.name] = read_signal_value_from_user(signal)

    frame_data = frame.encode(signalDict)
    if frame.arbitration_id.extended:
        print("{:05X}#".format(frame.arbitration_id.id) + "".join(["%02X" % i for i in frame_data]))
    else:
        print("{:03X}#".format(frame.arbitration_id.id) + "".join(["%02X" % i for i in frame_data]))
