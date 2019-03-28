import canmatrix.formats
import attr
import io
import textwrap

@attr.s
class j1939_decoder(object):
    length = attr.ib(default=0)  # type: int
    count_succesive_frames = attr.ib(default=0)  # type: int
    transfered_pgn = attr.ib(default=0)  # type: int
    _data = attr.ib(init=False, default=bytearray())

    def decode(self, arbitration_id, can_data, matrix):
        if canmatrix.J1939CanId(arbitration_id).pgn == 0xEC00 or canmatrix.J1939CanId(arbitration_id).pgn == 0xECFF:
            # BAM detected
            self.length = (int(can_data[2]) << 8) + int(can_data[1])
            self.count_succesive_frames = int(can_data[3])
            self.transfered_pgn = (int(can_data[7]) << 16) + (int(can_data[6]) << 8) + int(can_data[5])
            self.bytes_left = self.length
            self._data = bytearray()
            return ("BAM          ", {})

        if canmatrix.J1939CanId(arbitration_id).pgn == 0xEB00 or canmatrix.J1939CanId(arbitration_id).pgn == 0xEBFF:
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


test_j1939_decoder()

