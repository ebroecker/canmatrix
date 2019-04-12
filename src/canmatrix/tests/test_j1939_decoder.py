import io
import canmatrix.j1939_decoder
import textwrap
import collections

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

    t = canmatrix.j1939_decoder.j1939_decoder()

    #  BAM
    (type, signals) = t.decode(canmatrix.ArbitrationId(id = 0xec0000, extended= True),
        bytearray([0x20,10,0,1,0xff,0x66,0x1,0]), matrix)
    assert "BAM " in type
 #   print (type, signals)

    # data 1
    (type, signals) = t.decode(canmatrix.ArbitrationId(id = 0xeb0000, extended= True),
        bytearray([0x0,1,1,1,1,1,1,1]), matrix)
    assert "BAM data" in type
    #print (type, signals)

    # data 2
    (type, signals) = t.decode(canmatrix.ArbitrationId(id = 0xeb0000, extended= True),
        bytearray([0x1,1,1,1,1,1,1,1]), matrix)
    assert "BAM last data" in type
#    print (type, signals)


    can_ids = [0x18ECFF82, 0x18EBFF82, 0x18EBFF82]
    can_data = [bytearray([0x20, 9, 0, 2, 0xff, 0x20, 0xff, 0]),bytearray([0x1, 0, 0, 0, 0, 0x80, 0x0, 0x80]),bytearray([0x2, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])]
    #  BA0x20, M

    for i in range(0,len(can_ids)):
        (type, signals) = t.decode(canmatrix.ArbitrationId(id=can_ids[i], extended=True),
             can_data[i], matrix)

    print ("-------- test data -------- ")
    test_frames = collections.OrderedDict ([
        (0xcef27fd , "fffae1ff00ffff"),
        (0xcffcafd , "c0fffffffffff800"),
        (0xcf00203 , "cc00000000b812ff"),
        (0xfe4a03 , "fffcffffffffffff"),
        (0xc010305 , "ccfffaffff204e0a"),
        (0x0CF00400, "F4DEDE3028FFF0FF")])

    expected = ["EEC1","TC1","ETC7","ETC1"]
    for arb_id, asc_data in test_frames.items():
        (type, signals) = t.decode(canmatrix.ArbitrationId(id=arb_id, extended=True),
                                   bytearray.fromhex(asc_data), matrix)
        if type is not None and "J1939 known" in type:
            assert expected.pop() in type
