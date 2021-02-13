
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
--- Frame: muxTestFrame
muxTestFrame = Proto("muxTestFrame", "muxTestFrame") 
muxTestFrame_myMuxer = ProtoField.int32("can.muxTestFrame.myMuxer", "myMuxer", base.DEC)
muxTestFrame_muxSig4 = ProtoField.int32("can.muxTestFrame.muxSig4", "muxSig4", base.DEC)
muxTestFrame_muxSig3 = ProtoField.int32("can.muxTestFrame.muxSig3", "muxSig3", base.DEC)
muxTestFrame_muxSig2 = ProtoField.int32("can.muxTestFrame.muxSig2", "muxSig2", base.DEC)
muxTestFrame_muxSig1 = ProtoField.int32("can.muxTestFrame.muxSig1", "muxSig1", base.DEC)
muxTestFrame_muxSig5 = ProtoField.int32("can.muxTestFrame.muxSig5", "muxSig5", base.DEC)
muxTestFrame_muxSig6 = ProtoField.int32("can.muxTestFrame.muxSig6", "muxSig6", base.DEC)
muxTestFrame_muxSig7 = ProtoField.int32("can.muxTestFrame.muxSig7", "muxSig7", base.DEC)
muxTestFrame_muxSig8 = ProtoField.int32("can.muxTestFrame.muxSig8", "muxSig8", base.DEC)
muxTestFrame_muxSig9 = ProtoField.int32("can.muxTestFrame.muxSig9", "muxSig9", base.DEC)
muxTestFrame.fields = {muxTestFrame_myMuxer,muxTestFrame_muxSig4,muxTestFrame_muxSig3,muxTestFrame_muxSig2,muxTestFrame_muxSig1,muxTestFrame_muxSig5,muxTestFrame_muxSig6,muxTestFrame_muxSig7,muxTestFrame_muxSig8,muxTestFrame_muxSig9}

--- Frame: testFrameFloat
testFrameFloat = Proto("testFrameFloat", "testFrameFloat") 
testFrameFloat_floatSignal2 = ProtoField.float("can.testFrameFloat.floatSignal2", "floatSignal2")
testFrameFloat_floatSignal1 = ProtoField.float("can.testFrameFloat.floatSignal1", "floatSignal1")
testFrameFloat.fields = {testFrameFloat_floatSignal2,testFrameFloat_floatSignal1}

--- Frame: testFrame1
testFrame1 = Proto("testFrame1", "testFrame1") 
testFrame1_sig0 = ProtoField.int32("can.testFrame1.sig0", "sig0", base.DEC)
testFrame1_sig1 = ProtoField.int32("can.testFrame1.sig1", "sig1", base.DEC)
testFrame1_sig2 = ProtoField.int32("can.testFrame1.sig2", "sig2", base.DEC)
testFrame1_sig3 = ProtoField.int32("can.testFrame1.sig3", "sig3", base.DEC)
testFrame1_sig4 = ProtoField.int32("can.testFrame1.sig4", "sig4", base.DEC)
testFrame1_sig5 = ProtoField.int32("can.testFrame1.sig5", "sig5", base.DEC)
testFrame1_sig6 = ProtoField.int32("can.testFrame1.sig6", "sig6", base.DEC)
testFrame1_sig7 = ProtoField.int32("can.testFrame1.sig7", "sig7", base.DEC)
testFrame1_sig8 = ProtoField.int32("can.testFrame1.sig8", "sig8", base.DEC)
testFrame1_sig9 = ProtoField.int32("can.testFrame1.sig9", "sig9", base.DEC)
testFrame1_sig10 = ProtoField.int32("can.testFrame1.sig10", "sig10", base.DEC)
testFrame1.fields = {testFrame1_sig0,testFrame1_sig1,testFrame1_sig2,testFrame1_sig3,testFrame1_sig4,testFrame1_sig5,testFrame1_sig6,testFrame1_sig7,testFrame1_sig8,testFrame1_sig9,testFrame1_sig10}

--- Frame: testFrame2
testFrame2 = Proto("testFrame2", "testFrame2") 
testFrame2_secSig1 = ProtoField.int32("can.testFrame2.secSig1", "secSig1", base.DEC)
testFrame2_secSig2 = ProtoField.int32("can.testFrame2.secSig2", "secSig2", base.DEC)
testFrame2_secSig3 = ProtoField.int32("can.testFrame2.secSig3", "secSig3", base.DEC)
testFrame2_secSig4 = ProtoField.int32("can.testFrame2.secSig4", "secSig4", base.DEC)
testFrame2_secSig5 = ProtoField.int32("can.testFrame2.secSig5", "secSig5", base.DEC)
testFrame2_secSig6 = ProtoField.int32("can.testFrame2.secSig6", "secSig6", base.DEC)
testFrame2_secSig7 = ProtoField.int32("can.testFrame2.secSig7", "secSig7", base.DEC)
testFrame2_secSig8 = ProtoField.int32("can.testFrame2.secSig8", "secSig8", base.DEC)
testFrame2_secSig9 = ProtoField.int32("can.testFrame2.secSig9", "secSig9", base.DEC)
testFrame2_secSig10 = ProtoField.int32("can.testFrame2.secSig10", "secSig10", base.DEC)
testFrame2_secSig11 = ProtoField.int32("can.testFrame2.secSig11", "secSig11", base.DEC)
testFrame2_secSig12 = ProtoField.int32("can.testFrame2.secSig12", "secSig12", base.DEC)
testFrame2.fields = {testFrame2_secSig1,testFrame2_secSig2,testFrame2_secSig3,testFrame2_secSig4,testFrame2_secSig5,testFrame2_secSig6,testFrame2_secSig7,testFrame2_secSig8,testFrame2_secSig9,testFrame2_secSig10,testFrame2_secSig11,testFrame2_secSig12}

function add_frame_info(can_id, pdu, dlc, framesubtree)
  reversed_pdu = do_reverse_pdu(pdu, dlc)
  if can_id == 4 then
    local my_frame_tree = framesubtree:add(muxTestFrame, pdu(0, dlc))
    local is_signed
    local muxer = reversed_pdu:bitfield(0,3)
    if muxer == 0 then 
      is_signed =  reversed_pdu:bitfield(24,1)
      if is_signed == 1 then
        my_frame_tree:add(muxTestFrame_muxSig4, reversed_pdu:bitfield(24,7) - 128)
      else
        my_frame_tree:add(muxTestFrame_muxSig4, reversed_pdu:bitfield(24,7))
      end
    end
    if muxer == 0 then 
      my_frame_tree:add(muxTestFrame_muxSig3, reversed_pdu:bitfield(31,9))
    end
    if muxer == 0 then 
      is_signed =  pdu:bitfield(8,1)
      if is_signed == 1 then
        my_frame_tree:add(muxTestFrame_muxSig2, pdu:bitfield(8,8) - 256)
      else
        my_frame_tree:add(muxTestFrame_muxSig2, pdu:bitfield(8,8))
      end
    end
    if muxer == 0 then 
      is_signed =  reversed_pdu:bitfield(48,1)
      if is_signed == 1 then
        my_frame_tree:add(muxTestFrame_muxSig1, reversed_pdu:bitfield(48,8) - 256)
      else
        my_frame_tree:add(muxTestFrame_muxSig1, reversed_pdu:bitfield(48,8))
      end
    end
    if muxer == 1 then 
      is_signed =  reversed_pdu:bitfield(27,1)
      if is_signed == 1 then
        my_frame_tree:add(muxTestFrame_muxSig5, reversed_pdu:bitfield(27,7) - 128)
      else
        my_frame_tree:add(muxTestFrame_muxSig5, reversed_pdu:bitfield(27,7))
      end
    end
    if muxer == 1 then 
      my_frame_tree:add(muxTestFrame_muxSig6, reversed_pdu:bitfield(15,9))
    end
    if muxer == 1 then 
      is_signed =  pdu:bitfield(5,1)
      if is_signed == 1 then
        my_frame_tree:add(muxTestFrame_muxSig7, pdu:bitfield(5,8) - 256)
      else
        my_frame_tree:add(muxTestFrame_muxSig7, pdu:bitfield(5,8))
      end
    end
    if muxer == 1 then 
      is_signed =  reversed_pdu:bitfield(50,1)
      if is_signed == 1 then
        my_frame_tree:add(muxTestFrame_muxSig8, reversed_pdu:bitfield(50,6) - 64)
      else
        my_frame_tree:add(muxTestFrame_muxSig8, reversed_pdu:bitfield(50,6))
      end
    end
    is_signed =  reversed_pdu:bitfield(8,1)
    if is_signed == 1 then
      my_frame_tree:add(muxTestFrame_muxSig9, reversed_pdu:bitfield(8,8) - 256)
    else
      my_frame_tree:add(muxTestFrame_muxSig9, reversed_pdu:bitfield(8,8))
    end
  end
  if can_id == 3 then
    local my_frame_tree = framesubtree:add(testFrameFloat, pdu(0, dlc))
    local is_signed
    my_frame_tree:add(testFrameFloat_floatSignal2, reversed_pdu:bitfield(0,32))
    my_frame_tree:add(testFrameFloat_floatSignal1, pdu:bitfield(0,32))
  end
  if can_id == 1 then
    local my_frame_tree = framesubtree:add(testFrame1, pdu(0, dlc))
    local is_signed
    my_frame_tree:add(testFrame1_sig0, pdu:bitfield(6,2))
    my_frame_tree:add(testFrame1_sig1, pdu:bitfield(0,6))
    my_frame_tree:add(testFrame1_sig2, pdu:bitfield(8,11))
    my_frame_tree:add(testFrame1_sig3, pdu:bitfield(19,12))
    my_frame_tree:add(testFrame1_sig4, pdu:bitfield(31,9))
    my_frame_tree:add(testFrame1_sig5, pdu:bitfield(53,3))
    my_frame_tree:add(testFrame1_sig6, pdu:bitfield(50,3))
    my_frame_tree:add(testFrame1_sig7, pdu:bitfield(40,10))
    my_frame_tree:add(testFrame1_sig8, pdu:bitfield(61,3))
    my_frame_tree:add(testFrame1_sig9, pdu:bitfield(58,3))
    my_frame_tree:add(testFrame1_sig10, pdu:bitfield(56,2))
  end
  if can_id == 2 then
    local my_frame_tree = framesubtree:add(testFrame2, pdu(0, dlc))
    local is_signed
    my_frame_tree:add(testFrame2_secSig1, reversed_pdu:bitfield(2,2))
    my_frame_tree:add(testFrame2_secSig2, reversed_pdu:bitfield(8,1))
    my_frame_tree:add(testFrame2_secSig3, reversed_pdu:bitfield(40,4))
    my_frame_tree:add(testFrame2_secSig4, reversed_pdu:bitfield(0,2))
    my_frame_tree:add(testFrame2_secSig5, reversed_pdu:bitfield(27,3))
    my_frame_tree:add(testFrame2_secSig6, reversed_pdu:bitfield(24,3))
    is_signed =  reversed_pdu:bitfield(4,1)
    if is_signed == 1 then
      my_frame_tree:add(testFrame2_secSig7, reversed_pdu:bitfield(4,1) - 2)
    else
      my_frame_tree:add(testFrame2_secSig7, reversed_pdu:bitfield(4,1))
    end
    my_frame_tree:add(testFrame2_secSig8, reversed_pdu:bitfield(5,3))
    my_frame_tree:add(testFrame2_secSig9, reversed_pdu:bitfield(9,3))
    my_frame_tree:add(testFrame2_secSig10, reversed_pdu:bitfield(44,12))
    is_signed =  reversed_pdu:bitfield(30,1)
    if is_signed == 1 then
      my_frame_tree:add(testFrame2_secSig11, reversed_pdu:bitfield(30,10) - 1024)
    else
      my_frame_tree:add(testFrame2_secSig11, reversed_pdu:bitfield(30,10))
    end
    my_frame_tree:add(testFrame2_secSig12, reversed_pdu:bitfield(56,8))
  end
end

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
