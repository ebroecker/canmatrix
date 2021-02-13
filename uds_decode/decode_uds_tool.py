import can.io.logger
import tp_decode
import uds_decode

log_file = "some.asc"
req_id = 0x17FC00aa
res_id = 0x17FE00aa

my_decoder = tp_decode.tp_decoder(req_id, res_id)
reader = can.io.player.LogReader(log_file)

for msg in reader:
    direction, decoded = my_decoder.decode(msg)
    if len(decoded) > 0:
        print(direction + ": " + uds_decode.decode_uds(decoded) + "\t\t[" + " ".join([hex(i) for i in decoded]) + "]")
