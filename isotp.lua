--
-- This Script adds a SubDissector for the Wireshark CAN Dissector
-- It gets called for every data section
-- Its just a test and proof of concept
--

--we need this field from the CAN dissector
--local can_identifier = Field.new("can.id")
--local tree = root:add(my_iso_tp_subdissector, tvbuf:range(0,pktlen))
-- Retrieve the CAN identifier
--local can_id_hex = can_identifier()
--local can_id_hex_string = tostring(can_id_hex)

--Create new Protocol, doesnt register it yet
local my_iso_tp_subdissector = Proto.new("isotp", "ISO-TP")
print("myISOTP Created")

-- create a protocol field (but not register it yet)
--ProtoField.new(name, abbr, type, [voidstring], [base], [mask], [descr])
--ProtoField.new   ("Authoritative", "mydns.flags.authoritative", ftypes.BOOLEAN, nil, 16, 0x0400, "is the response authoritative?")
local tp_identifier = ProtoField.new("FrameType", "isotp.ftype", ftypes.UINT8, nil,base.DEC,0xF0,"TP identifier")
local tp_pci = ProtoField.new("PCI", "isotp.pci", ftypes.BYTES)

--SINGLE FRAMES
local tp_sf_identifier = 0
local tp_sf_pci_byte_length = 1
local tp_sf_datalength = ProtoField.new("DataLength", "isotp.sdl", ftypes.UINT8, nil,base.DEC,0x0F,"TP DataLength")

--FIRST FRAMES
local tp_ff_identifier = 1
local tp_ff_pci_byte_length = 2
local tp_ff_datalength = ProtoField.new("DataLength", "isotp.fdl", ftypes.UINT16, nil,base.DEC,0x0FFF,"TP DataLength")

--CONSECUTIVE FRAMES
local tp_cf_identifier = 2
local tp_cf_pci_byte_length = 1
local tp_cf_sequence_number = ProtoField.new("Sequencenumber", "isotp.sn", ftypes.UINT8, nil,base.DEC,0x0F,"TP SequenceNumber")
local tp_

--FLOW CONTROL FRAME
local tp_fcf_identifier = 3
local tp_fcf_pci_byte_length = 3
local tp_fcf_flow_status = ProtoField.new("FlowStatus", "isotp.fs", ftypes.UINT24, nil,base.DEC,0x0F0000,"TP Flow Status")
local tp_fcf_block_size = ProtoField.new("BlockSize", "isotp.bs", ftypes.UINT24, nil,base.DEC,0x00FF00,"TP Block Size")
local tp_fcf_min_sep_time = ProtoField.new("BlockSize", "isotp.bs", ftypes.UINT24, nil,base.DEC,0x0000FF,"TP Minimum Separation Time")
local FCF_FLOW_STATUS = {
    OVERFLOW = 2,
    SEND = 1,
    WAIT = 0
}

--local pf_test = ProtoField.new("Test", "mycan.test", ftypes.UINT8, nil, base.HEX)
print("ProtFields Created")

-- this actually registers the ProtoFields above, into our new Protocol
-- in a real script I wouldn't do it this way; I'd build a table of fields programmatically
-- and then set dns.fields to it, so as to avoid forgetting a field
my_iso_tp_subdissector.fields = {
    tp_pci,
    tp_identifier,
    tp_sf_datalength,
    tp_ff_datalength,
    tp_cf_sequence_number,
    tp_fcf_flow_status,
    tp_fcf_block_size,
    tp_fcf_min_sep_time
}
print("MyISO-TP Added")


function my_iso_tp_subdissector.dissector(tvbuf,pktinfo,root)

    -- set the protocol column to show our protocol name
    pktinfo.cols.protocol:set("ISO-TP")

    local pktlen = tvbuf:reported_length_remaining()
    local frame_ident = tvbuf:range(0,1):bitfield(0,4)

    if frame_ident == tp_sf_identifier then

        local tree = root:add(my_iso_tp_subdissector, tvbuf:range(0,tp_sf_pci_byte_length))

        local pci = tvbuf:range(0,tp_sf_pci_byte_length)

        -- Add items to tree
        local pci_tree = tree:add(tp_pci, pci)

        pci_tree:add(tp_identifier, pci)
        pci_tree:add(tp_sf_datalength, pci)

    elseif frame_ident == tp_ff_identifier then

        local tree = root:add(my_iso_tp_subdissector, tvbuf:range(0,tp_ff_pci_byte_length))

        local pci = tvbuf:range(0,tp_ff_pci_byte_length)

        -- Add items to tree
        local pci_tree = tree:add(tp_pci, pci)

        pci_tree:add(tp_identifier, pci)
        pci_tree:add(tp_ff_datalength, pci)

    elseif frame_ident == tp_cf_identifier then

        local tree = root:add(my_iso_tp_subdissector, tvbuf:range(0,tp_cf_pci_byte_length))

        local pci = tvbuf:range(0,tp_cf_pci_byte_length)

        -- Add items to tree
        local pci_tree = tree:add(tp_pci, pci)

        pci_tree:add(tp_identifier, pci)
        pci_tree:add(tp_cf_sequence_number, pci)

    elseif frame_ident == tp_fcf_identifier then
        local tree = root:add(my_iso_tp_subdissector, tvbuf:range(0,tp_fcf_pci_byte_length))

        local pci = tvbuf:range(0,tp_fcf_pci_byte_length)

        -- Add items to tree
        local pci_tree = tree:add(tp_pci, pci)

        pci_tree:add(tp_fcf_flow_status, pci)
        pci_tree:add(tp_fcf_block_size, pci)
        pci_tree:add(tp_fcf_min_sep_time, pci)
    else
      print("Unknown frame identifier")
    end


end

----------------------------------------
--add our dissector as a subdissector for the standard CAN dissector
dissector = DissectorTable.get("can.subdissector")
dissector:add_for_decode_as(my_iso_tp_subdissector)

print("MyISO-TP Registered")

