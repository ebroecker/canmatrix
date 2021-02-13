import tp_decode
import can.io.logger
log_file = "some.asc"
req_id = 0x17FC00aa
res_id = 0x17FE00aa

my_decoder = tp_decode.tp_decoder(req_id, res_id)
reader = can.io.player.LogReader(log_file)

for msg in reader:
    direction, decoded = my_decoder.decode(msg)
    if len(decoded) > 0:
        print(direction + ": " + " ".join([hex(i) for i in decoded]))
