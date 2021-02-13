import canmatrix.formats

cm = canmatrix.formats.loadp_flat("/home/edu/Downloads/CSS-Electronics-OBD2-v1.4.dbc")

arbitration_id = canmatrix.ArbitrationId(id=2024, extended=False)
data = bytearray([0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA])

frame = cm.frame_by_id(arbitration_id)

a = frame.decode(data)
print(a)

b = cm.decode(arbitration_id, data)
print(b)