# -*- coding: utf-8 -*-
from __future__ import absolute_import

import canmatrix.formats
import pathlib2
import attr

@attr.s
class j1939_decoder(object):
    here = pathlib2.Path(__file__).parent

    j1939_db = canmatrix.formats.loadp_flat(str(here / "j1939.dbc"), dbcImportEncoding = "utf8")
    length = attr.ib(default=0)  # type: int
    count_succesive_frames = attr.ib(default=0)  # type: int
    transfered_pgn = attr.ib(default=0)  # type: int
    _data = attr.ib(init=False, default=bytearray())

    def decode(self, arbitration_id, can_data, matrix = None):
        if matrix is not None:
            frame = matrix.frame_by_pgn(arbitration_id.pgn)
        else:
            frame = None
        if frame is not None:
            return ("regular " + frame.name, frame.decode(can_data))
        elif self.j1939_db.frame_by_pgn(arbitration_id.pgn) is not None:
            signals = self.j1939_db.decode(arbitration_id,can_data)
            frame_name = self.j1939_db.frame_by_pgn(arbitration_id.pgn).name
            return ("J1939 known: " + frame_name, signals)

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 32:
            # BAM detected
            self.length = (int(can_data[2]) << 8) + int(can_data[1])
            self.count_succesive_frames = int(can_data[3])
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])
            self.bytes_left = self.length
            self._data = bytearray()
            return ("BAM          ", {})

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 16:
            # RTS detected
            self.length = (int(can_data[2]) << 8) + int(can_data[1])
            self.count_of_packets = int(can_data[3])
            self.total_count_of_packet_sent = int(can_data[4])
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])
            return ("ERROR - decoding RTS not yet implemented")

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 17:
            # CTS detected
            self.max_packets_at_once = can_data[1]
            self.sequence_number_to_start = can_data[2]
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])
            return ("ERROR - decoding CTS not yet implemented")

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 19:
            # ACK detected
            self.message_size = (int(can_data[2]) << 8) + int(can_data[1])
            self.count_of_packets = int(can_data[3])
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])
            return ("ERROR - decoding ACK not yet implemented")

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 255:
            # Connection Abort
            self.abort_reason = can_data[1]
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])
            return ("ERROR - decoding Connection Abbort not yet implemented")


        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xEEFF).pgn:
            #Address Claimed
            #arbitration_id.j1939_source
            #name in can_data[0:8]
            return ("ERROR - address claim detected not yet implemented")
            pass

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xEBFF).pgn:
            # transfer data

            self._data = self._data + can_data[1:min(8, self.bytes_left + 1)]
            self.bytes_left = max(self.bytes_left - 7, 0)

            if self.count_succesive_frames == 0:
                #print(self._data)
                frame = matrix.frame_by_pgn(self.transfered_pgn)
                if frame is not None:
                    signals = frame.decode(self._data)
                    return ("BAM last data", signals)
                return ("BAM last data", {})
            else:
                self.count_succesive_frames -= 1
                return ("BAM data     ", {})
        return ("",{})



