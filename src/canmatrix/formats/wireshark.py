# Copyright (c) 2019, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

#
# this script exports lua files for use with wireshark as dissector

import textwrap
import typing

import canmatrix

extension = "lua"


def get_coorect_bits_for_signal(frame, signal, signal_size = None):
    if not signal_size:
        signal_size = signal.size
    if signal.is_little_endian:
        name_of_bitfield = "reversed_pdu"
        start_bit = (frame.size*8) - signal.start_bit - signal.size
    else:
        name_of_bitfield = "pdu"
        start_bit = signal.start_bit
    return '{}:bitfield({},{})'.format(name_of_bitfield, start_bit , signal_size)

def create_dissect_signal(frame, signal, indent = 0):
    dissector_string = ""

    bits_for_signal = get_coorect_bits_for_signal(frame, signal)

    if signal.is_signed and not signal.is_float:
        dissector_string += ' '*indent + '    is_signed =  {}\n'.format(get_coorect_bits_for_signal(frame, signal, 1))
        dissector_string += ' '*indent +'    if is_signed == 1 then\n'
        dissector_string += ' '*indent +'      my_frame_tree:add({}_{}, {} - {})\n'.format(frame.name, signal.name, bits_for_signal, 1 << signal.size)
        dissector_string += ' '*indent +'    else\n'
        dissector_string += ' '*indent +'      my_frame_tree:add({}_{}, {})\n'.format(frame.name, signal.name, bits_for_signal)
        dissector_string += ' '*indent +'    end\n'
    else:
        dissector_string += ' '*indent + "    my_frame_tree:add({}_{}, {})\n".format(frame.name, signal.name, bits_for_signal)
    return dissector_string


def dump(db, f, **options):  # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    wireshark_dissector = textwrap.dedent("""
    --- lua dissector exported by canmatrix
    --- may be buggy. currently float decoding is corrupt
    --- if you see this and want to improve the lua code please help at github.com/ebroecker/canamtrix
    
    --- global function for reversing pdu
    --- helper is needed to decode little endian
    function do_reverse_pdu(pdu, length)
        local rev=ByteArray.new()
        rev:set_size(length)
        
        for i=0,length-1 do
            rev:set_index(length-i-1, pdu(i,1):uint())
        end
        return ByteArray.tvb(rev, "my Tvb"):range(0,length)                                                      
        
    end
    """)


    for frame in db.frames:
        wireshark_dissector += "--- Frame: {}\n".format(frame.name)
        wireshark_dissector += '{} = Proto("{}", "{}") \n'.format(frame.name, frame.name, frame.name)

        for signal in frame.signals:
            if signal.is_float:
                wireshark_dissector += u'{}_{} = ProtoField.float("can.{}.{}", "{}")\n'.format(frame.name,
                                                                                                         signal.name,
                                                                                                         frame.name,
                                                                                                         signal.name,
                                                                                                         signal.name)
            else:
                wireshark_dissector += u'{}_{} = ProtoField.int32("can.{}.{}", "{}", base.DEC)\n'.format(frame.name, signal.name, frame.name, signal.name, signal.name)

        wireshark_dissector += "{}.fields = {{".format(frame.name)
        wireshark_dissector += ",".join([frame.name + "_" + s.name for s in frame.signals])
        wireshark_dissector += "}\n\n"


    wireshark_dissector += "function add_frame_info(can_id, pdu, dlc, framesubtree)\n"
    wireshark_dissector += "  reversed_pdu = do_reverse_pdu(pdu, dlc)\n"

    for frame in db.frames:
        wireshark_dissector += "  if can_id == {} then\n".format(frame.arbitration_id.id)
        wireshark_dissector += "    local my_frame_tree = framesubtree:add({}, pdu(0, dlc))\n".format(frame.name)
        wireshark_dissector += "    local is_signed\n"
        if frame.is_multiplexed and not frame.is_complex_multiplexed:
            multiplexer = frame.get_multiplexer
            wireshark_dissector += u'    local muxer = {}\n'.format(get_coorect_bits_for_signal(frame,multiplexer))
            for signal in frame.signals:
                if signal != multiplexer and signal.mux_val is not None:
                    wireshark_dissector += '    if muxer == {} then \n'.format(signal.mux_val)
                    wireshark_dissector += create_dissect_signal(frame, signal, indent=2)
                    wireshark_dissector += '    end\n'
                elif signal != multiplexer:
                    wireshark_dissector += create_dissect_signal(frame, signal)
        else:
            for signal in frame.signals:
                wireshark_dissector += create_dissect_signal(frame, signal)
        wireshark_dissector += "  end\n"

    wireshark_dissector += "end\n"

    wireshark_dissector += textwrap.dedent("""
    local can_database_decoder = Proto.new("CanSignalDecoder", "Can Signal Decoder")
    can_database_can_id = ProtoField.uint32("can.frame.arbitration_id", "can_id", base.HEX)
    can_database_decoder.fields = {can_database_can_id}

    local f_can_id = Field.new("can.id")

    function can_database_decoder.dissector(buffer, pinfo, tree)
      local can_id = f_can_id()
      local pktlen = buffer:reported_length_remaining()
      add_frame_info(can_id.tvb:le_uint(), buffer(0, pktlen), pktlen, tree)
    end

    DissectorTable.get("can.subdissector"):add_for_decode_as(can_database_decoder)
    """)

    f.write(wireshark_dissector.encode("utf8"))
