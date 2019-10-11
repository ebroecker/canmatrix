--- dissects cannelloni packages
--- https://github.com/mguentner/cannelloni
--- https://github.com/PhilippFux/cannelloni
---
--- canneloni frame
cannelloni_protocol = Proto("Cannelloni", "Can over UPD Cannelloni")

cannelloni_version = ProtoField.int8("canneloni.version", "version", base.DEC)
cannelloni_opcode = ProtoField.int8("canneloni.opcode", "opcode", base.DEC)
cannelloni_seq_no = ProtoField.int8("canneloni.seq_no", "seq_no", base.DEC)
cannelloni_count = ProtoField.int16("canneloni.count", "count", base.DEC)
cannelloni_protocol.fields = {cannelloni_version, cannelloni_opcode, cannelloni_seq_no, cannelloni_count}

--- Can Frame
can_frame = Proto("MyFrame", "My Can Frame")
can_frame_id = ProtoField.uint32("can.frame.arbitration_id", "can_id", base.HEX)
can_frame_is_extended = ProtoField.string("can.frame.is_extended", "is_extended")
can_frame_dlc  = ProtoField.uint8("can.frame.dlc", "dlc", base.DEC)
can_frame_pdu = ProtoField.uint64("can.frame.pdu", "pdu", base.HEX)
can_frame.fields = {can_frame_id, can_frame_is_extended, can_frame_dlc, can_frame_pdu}

--- select your database - generated with canmatrix  here [canconvert some.dbc can_database.lua]
require "can_database"
            
debug_example_protocol = false                                                       
cannelloni_header_offset = 5                            
 
function cannelloni_protocol.dissector(buffer, pinfo, tree)
  length = buffer:len()
  if length == 0 then return end

  pinfo.cols.protocol = cannelloni_protocol.name

  local subtree = tree:add(cannelloni_protocol, buffer(), "Cannelloni Protocol Data")
  subtree:add(cannelloni_version, buffer(0,1))
  subtree:add(cannelloni_opcode, buffer(1,1))
  subtree:add(cannelloni_seq_no, buffer(2,1))
  subtree:add(cannelloni_count, buffer(3,2))
  
  local count = buffer(3,2):uint()
  buffer_offset = cannelloni_header_offset
  
  --- each frame:
  for i=1,count do
      local framesubtree = subtree:add(can_frame, buffer(), "Can Frame" .. tostring(i))
  
      can_id = buffer(buffer_offset,4)
      framesubtree:add(can_frame_id, can_id:bitfield(1,31))
      if can_id:bitfield(0,1) == 1 then 
        framesubtree:add(can_frame_is_extended, "True")
      else 
        framesubtree:add(can_frame_is_extended, "False") 
      end
      
      framesubtree:add(can_frame_dlc, buffer(buffer_offset+4,1))  
      local dlc = buffer(buffer_offset+4,1):uint()
      
      pdu = buffer(buffer_offset+5,dlc)
      framesubtree:add(can_frame_pdu, pdu)  
      add_frame_info(can_id:uint(), pdu, dlc, framesubtree) 
      
      buffer_offset = buffer_offset + 4 + 1 + dlc
  end
end

example_add_tree_info = true

local udp_port = DissectorTable.get("udp.port")
udp_port:add(3333, cannelloni_protocol)