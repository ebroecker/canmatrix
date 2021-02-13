
UDS_SID = {
    0x10: "Diagnostic Session Control",
    0x3E: "Tester Present",
    0x27: "Security Access",
    0x11: "ECU Reset",
    0x28: "Communication Control",
    0x85: "Control DTC Setting",
    0x83: "Access Timing Parameters",
    0x87: "Link Control",
    0x86: "Response On Event Service",
    0x22: "Read Data By Identifier",
    0x23: "Read Memory By Address",
    0x2E: "Write Data By Identifier",
    0x3D: "Write Memory By Address",
    0x2A: "Read Daty By Periodic Identifier",
    0x14: "Clear Diagnostic Inforamtion",
    0x19: "Read DTC Information",
    0x2F: "Input Output Control By Identifier",
    0x31: "Routine Control",
    0x34: "Request Download",
    0x35: "Request Upload",
    0x36: "Transfer Data",
    0x37: "Request Transfer Exit",
}

UDS_NRC = {
    0x10: "General reject",
    0x11: "Service not supported",
    0x12: "Subfuntion not supported",
    0x13: "Incorrect message length/invalid format",
    0x14: "Response to long",
    0x21: "Busy Repeat Request",
    0x22: "Conditions not correct",
    0x24: "Request sequence Error",
    0x25: "No Response from subnet component",
    0x26: "Failure prevents execution of request action",
    0x31: "Request out of range",
    0x33: "Security access denied",
    0x35: "Invalid key",
    0x36: "Exceeds number of attempts",
    0x37: "Required time delay not expired",
    0x70: "Upload download not accepted",
    0x71: "Transfer data suspended",
    0x72: "General programming failure",
    0x73: "Wrong block sequence counter",
    0x78: "Response pending",
    0x7E: "Subfunction not supported in active session",
    0x7F: "Service not supported in active session",
    0x81: "Rpm to high",
    0x82: "Rpm to low",
    0x83: "Engine is running",
    0x84: "Engine is not running",
    0x85: "Engine runtime to low",
    0x86: "Temperature to high",
    0x87: "Temperature to low",
    0x88: "Vehicle speed to high",
    0x89: "Vehicle speed to low",
    0x8A: "Throttle pedal to high",
    0x8B: "Throttle pedal to low",
    0x8C: "Transmission range not in neutral",
    0x8D: "Transmission range not in gear"
}

def decode_uds(data):
    first_byte = data[0]

    if first_byte in UDS_SID:
        return (UDS_SID[first_byte])
    elif first_byte-0x40 in UDS_SID:
        return ("Positiv Response to {" + UDS_SID[first_byte-0x40] + "}")
    elif first_byte == 0x7F:
        second_byte = data[1]
        third_byte = data[2]
        return ("negative Response to {" + UDS_SID[second_byte] + "} : {" + UDS_NRC[third_byte] + "}")
    return ""



