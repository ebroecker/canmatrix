import canmatrix.formats
import sys

#cm1 = canmatrix.formats.loadp_flat("src/canmatrix/formats/aa.dbc")

#cm = canmatrix.CanMatrix()
#my_frame = canmatrix.Frame("SDO_TX")
#my_frame.is_complex_multiplexed = True
#cm.add_frame(my_frame)

#my_sig1 = canmatrix.Signal("CMD_CCS", multiplex="Multiplexor")
#my_frame.add_signal(my_sig1)

#my_sig2 = canmatrix.Signal("Index")
#my_sig2.is_multiplexer = True
#my_sig2.multiplex = 'Multiplexor'
#my_sig2.mux_val = 2
#my_sig2.muxer_for_signal = "CMD_CSS"
#my_sig2.mux_val_grp.append( [81159, 81159])
#my_frame.add_signal(my_sig2)

#canmatrix.formats.dumpp({"": cm}, "bb.dbc")

#for file in ["1115.eds", "HE-927325-0002.eds",  "QG_Ftype_3_axis_8g_v6.2.eds" , "sw001454.eds"]:
#file = "1115.eds"
#cm =canmatrix.formats.loadp_flat("/home/edu/Downloads/eds/" + file)


#for frame in cm.frames:
#    for sig in frame.signals:
#        print(sig.name)

#sys.exit(0)
import canopen

# Define the Node ID (default is 0)
node_id = 0

# Load the EDS file into the object dictionary
print("Loading EDS file...")
object_dictionary = canopen.import_od("/home/edu/Downloads/eds/" + "1115.eds", node_id=node_id)
print("EDS file loaded successfully.")

# CANopen data type mapping
DATA_TYPE_NAMES = {
    0x01: "BOOLEAN",
    0x02: "INTEGER8",
    0x03: "INTEGER16",
    0x04: "INTEGER32",
    0x05: "UNSIGNED8",
    0x06: "UNSIGNED16",
    0x07: "UNSIGNED32",
    0x08: "REAL32",
    0x09: "VISIBLE_STRING",
    0x0A: "OCTET_STRING",
    0x0B: "UNICODE_STRING",
    0x0C: "TIME_OF_DAY",
    0x0D: "TIME_DIFFERENCE",
    0x0F: "DOMAIN",
    0x10: "INTEGER24",
    0x11: "REAL64",
    0x12: "INTEGER40",
    0x13: "INTEGER48",
    0x14: "INTEGER56",
    0x15: "INTEGER64",
    0x16: "UNSIGNED24",
    0x18: "UNSIGNED40",
    0x19: "UNSIGNED48",
    0x1A: "UNSIGNED56",
    0x1B: "UNSIGNED64",
}

def get_data_type_name(data_type_code):
    return DATA_TYPE_NAMES.get(data_type_code, f"Unknown (0x{data_type_code:X})")

def format_index(index, subindex):
    return f"Index: 0x{index:04X}{subindex:02X}"

def get_bit_length(data_type_code):
    # Extract bit length based on the data type name
    data_type_name = get_data_type_name(data_type_code)
    if "INTEGER" in data_type_name or "UNSIGNED" in data_type_name or "REAL" in data_type_name:
        return int(data_type_name.split("INTEGER")[-1].split("UNSIGNED")[-1].split("REAL")[-1])
    elif data_type_name == "BOOLEAN":
        return 1
    else:
        return "N/A"

def list_all_objects(od):
    print("\nListing all objects in the Object Dictionary:")
    for obj in od.values():
        if "Record" in obj.name.replace(' ', '_'):
            print("BEEP")
        if isinstance(obj, canopen.objectdictionary.ODVariable):
            subindex = 0
            combined_value = int(f"{subindex:02X}{obj.index:04X}", 16)
            print(f"\n{format_index(obj.index, subindex)}")
            print(f"  M: {combined_value}")
            print(f"  Subindex (dec): {subindex}")
            print(f"  Name: {obj.name.replace(' ', '_')}")
            print(f"  Bit Length: {get_bit_length(obj.data_type)}")
            print(f"  Type: Variable")
            print(f"  Data Type: {get_data_type_name(obj.data_type)}")
            print(f"  Access Type: {obj.access_type}")
            print(f"  Default Value: {obj.default}")
        elif isinstance(obj, canopen.objectdictionary.ODRecord):
            for subobj in obj.values():
                if subobj.name.replace(' ', '_') == "Record":
                    print("BEEP")
                combined_value = int(f"{subobj.subindex:02X}{obj.index:04X}", 16)
                print(f"\n{format_index(obj.index, subobj.subindex)}")
                print(f"  M: {combined_value}")
                print(f"  Subindex (dec): {subobj.subindex}")
                print(f"  Name: {subobj.name.replace(' ', '_')}")
                print(f"  Bit Length: {get_bit_length(subobj.data_type)}")
                print(f"  Type: Record")
                print(f"  Data Type: {get_data_type_name(subobj.data_type)}")
                print(f"  Access Type: {subobj.access_type}")
                print(f"  Default Value: {subobj.default}")
        elif isinstance(obj, canopen.objectdictionary.ODArray):
            for subobj in obj.values():
                if subobj.name.replace(' ', '_') == "Record":
                    print("BEEP")
                combined_value = int(f"{subobj.subindex:02X}{obj.index:04X}", 16)
                print(f"\n{format_index(obj.index, subobj.subindex)}")
                print(f"  M: {combined_value}")
                print(f"  Subindex (dec): {subobj.subindex}")
                print(f"  Name: {subobj.name.replace(' ', '_')}")
                print(f"  Bit Length: {get_bit_length(subobj.data_type)}")
                print(f"  Type: Array")
                print(f"  Data Type: {get_data_type_name(subobj.data_type)}")
                print(f"  Access Type: {subobj.access_type}")
                print(f"  Default Value: {subobj.default}")
        

# List all objects in the Object Dictionary
list_all_objects(object_dictionary)