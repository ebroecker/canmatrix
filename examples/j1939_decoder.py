import canmatrix.formats
from pathlib2 import Path
import attr
import io
import textwrap

@attr.s
class j1939_decoder(object):
    here = pathlib2.Path(__file__).parent

    j1939_db = canmatrix.formats.loadp_flat(str(here / "j1939.dbc"), dbcImportEncoding = "utf8")
    length = attr.ib(default=0)  # type: int
    count_succesive_frames = attr.ib(default=0)  # type: int
    transfered_pgn = attr.ib(default=0)  # type: int
    _data = attr.ib(init=False, default=bytearray())

    def decode(self, arbitration_id, can_data, matrix):
        frame = matrix.frame_by_pgn(canmatrix.ArbitrationId(id=can_id, extended=True).pgn)
        if frame is not None:
            return ("regular", frame.decode(can_data))
        elif self.j1939_db.frame_by_pgn(arbitration_id.pgn) is not None:
            frame = self.j1939_db.frame_by_pgn(arbitration_id.pgn)
            signals = frame.decode(can_data)
            return ("J1939 known: " + frame.name + " " + frame.comment, signals)

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

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 17:
            # CTS detected
            self.max_packets_at_once = can_data[1]
            self.sequence_number_to_start = can_data[2]
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 19:
            # ACK detected
            self.message_size = (int(can_data[2]) << 8) + int(can_data[1])
            self.count_of_packets = int(can_data[3])
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xECFF).pgn and can_data[0] == 255:
            # Connection Abort
            self.abort_reason = can_data[1]
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xEEFF).pgn:
            #Address Claimed
            #arbitration_id.j1939_source
            #name in can_data[0:8]
            pass

        elif arbitration_id.pgn == canmatrix.ArbitrationId.from_pgn(0xEBFF).pgn:
            # transfer data
            self.count_succesive_frames -= 1

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
                return ("BAM data     ", {})
        return ("",{})


def test_j1939_decoder():
    dbc = io.BytesIO(textwrap.dedent(u'''\
       BO_ 2566856834 CM_Requests: 9 CGW
    SG_ CM_Inlet_MotorRequest : 50|2@0+ (1,0) [0|3] "" CM
    SG_ CM_ChargeUnit_Request : 52|2@0+ (1,0) [0|3] "" CM
    SG_ CM_RTC_TimerValue : 47|8@0+ (1,0) [0|254] "min" CM
    SG_ CM_RTC_TimerRequest : 37|2@0+ (1,0) [0|3] "" CM
    SG_ CM_PlugLock_MotorRequest : 35|3@0+ (1,0) [0|7] "" CM
    SG_ CM_LED2_Request : 23|8@0+ (0.5,0) [0|100] "%" CM
    SG_ CM_LED1_Request : 15|8@0+ (0.5,0) [0|100] "%" CM
    SG_ CM_LED0_Request : 7|8@0+ (0.5,0) [0|100] "%" CM
    SG_ CM_HighSideOut4_Request : 39|2@0+ (1,0) [0|3] "" CM
    SG_ CM_HighSideOut3_Request : 25|2@0+ (1,0) [0|3] "" CM
    SG_ CM_HighSideOut2_Request : 27|2@0+ (1,0) [0|3] "" CM
    SG_ CM_HighSideOut1_Request : 29|2@0+ (1,0) [0|3] "" CM
    SG_ CM_HighSideOut0_Request : 31|2@0+ (1,0) [0|3] "" CM
    SG_ CM_ControlPilot_ChargeModeRe : 55|3@0+ (1,0) [0|7] "" CM
       ''').encode('utf-8'))
    matrix = canmatrix.formats.dbc.load(dbc, dbcImportEncoding="utf8")

    t = j1939_decoder()

    #  BAM
    (type, signals) = t.decode(canmatrix.ArbitrationId(id = 0xec0000, extended= True),
        bytearray([0x20,10,0,1,0xff,0x66,0x1,0]), matrix)
    print (type, signals)

    # data 1
    (type, signals) = t.decode(canmatrix.ArbitrationId(id = 0xeb0000, extended= True),
        bytearray([0x0,1,1,1,1,1,1,1]), matrix)
    print (type, signals)

    # data 2
    (type, signals) = t.decode(canmatrix.ArbitrationId(id = 0xeb0000, extended= True),
        bytearray([0x1,1,1,1,1,1,1,1]), matrix)
    print (type, signals)


    can_ids = [0x18ECFF82, 0x18EBFF82, 0x18EBFF82]
    can_data = [bytearray([0x20, 9, 0, 2, 0xff, 0x20, 0xff, 0]),bytearray([0x1, 0, 0, 0, 0, 0x80, 0x0, 0x80]),bytearray([0x2, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])]
    #  BA0x20, M

    for i in range(0,len(can_ids)):
        (type, signals) = t.decode(canmatrix.ArbitrationId(id=can_ids[i], extended=True),
             can_data[i], matrix)
        print (type,"\t" , " ".join(["%02X" % x for x in can_data[i]]))

        for signal, value in signals.items():
            print (signal + " " + str(value.raw_value))

    print ("-------- test data -------- ")
    test_frames =   {
        0xcef27fd : "fffae1ff00ffff",
        0xcffcafd : "c0fffffffffff800",
        0xcf00203 : "cc00000000b812ff",
        0xfe4a03 : "fffcffffffffffff",
        0xc010305 : "ccfffaffff204e0a",
        0x0CF00400: "F4DEDE3028FFF0FF"}

    for arb_id, asc_data in test_frames.items():
        (type, signals) = t.decode(canmatrix.ArbitrationId(id=arb_id, extended=True),
                                   bytearray.fromhex(asc_data), matrix)
        if type is not None:
            print (type)
            for sig,decoded in signals.items():
                print (" " + decoded.signal.name + " " + str(decoded.raw_value))


test_j1939_decoder()

