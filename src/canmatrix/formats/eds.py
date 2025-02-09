import logging
import canmatrix
import typing
import canopen.objectdictionary.eds
import canopen.objectdictionary.datatypes
import codecs
import copy
import re 
import math

logger = logging.getLogger(__name__)


datatype_mapping = {0x1: ["boolean", 1], 
                    0x2: ["INTEGER8", 0x2],
                    0x3 : ["INTEGER16", 16],
                    0x4 : ["INTEGER32", 32],
                    0x5: ["UNSIGNED8" , 8],
                    0x6: ["UNSIGNED16" , 16],
                    0x7: ["UNSIGNED32" , 32],
                    0x8: ["REAL32" , 32],
                    0x9: ["VISIBLE_STRING", 0], 
                    0xA: ["OCTET_STRING" , 0],
                    0xB: ["UNICODE_STRING" , 0],
                    0xF: ["DOMAIN" , 0],
                    0x11: ["REAL64" , 64],
                    0x15: ["INTEGER64" , 64],
                    0x1B: ["UNSIGNED64", 64],
                    }

cmd_values = {  1: 'switch to state "Operational"',
                2 : 'switch to state "Stop"',
                0x80 : 	'switch to state "Pre-Operational"',
                0x81 :	'Reset Node',
                0x82: 	'Reset Communication'}


def name_cleanup(in_str):
    rets_str = re.sub("[^A-Za-z0-9]", '_', in_str)
    return rets_str

def get_bit_length(data_type_code):
    return  datatype_mapping[data_type_code][1]
def get_data_type_name(data_type_code):
    return  datatype_mapping[data_type_code][0]
    
def format_index(index, subindex):
    return f"Index: 0x{index:04X}{subindex:02X}"

def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    eds_import_encoding = options.get("edsImportEncoding", 'iso-8859-1')
    node_id = options.get("eds_node_id", 0)
    generic = options.get("generic", False)
    fp = codecs.getreader(eds_import_encoding)(f)
    od = canopen.objectdictionary.eds.import_eds(fp, node_id)
    db = canmatrix.CanMatrix()
    signal_group_counter = 1

    node_name = od.device_information.product_name
    if len(node_name) == 0:
        node_name = "DUMMY"
    plc_name = "PLC"
    if generic is True:
        nm_out = canmatrix.canmatrix.Frame(name="NMT_Out_Request", size=2, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0), transmitters=[plc_name])
        sig_cmd = canmatrix.canmatrix.Signal(name="nmt_CMD", size=8, start_bit = 0, receivers=[node_name])
        for val, val_name in cmd_values.items():
            sig_cmd.add_values(val, val_name)
        nm_out.add_signal(sig_cmd)
        nm_out.add_signal(canmatrix.canmatrix.Signal(name="Node_ID", size=8, start_bit = 8, receivers=[node_name]))
        db.add_frame(nm_out)

        nm_responde = canmatrix.canmatrix.Frame(name="NMT_Response_Frame_In", size=8, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0x700+node_id), transmitters=[node_name])
        response_sig1 = canmatrix.canmatrix.Signal(name="NMT_Response_1", size=32, start_bit = 0, receivers=[plc_name])
        nm_responde.add_signal(response_sig1)
        response_sig2 = canmatrix.canmatrix.Signal(name="NMT_Response_1", size=32, start_bit = 32, receivers=[plc_name])
        nm_responde.add_signal(response_sig2)
        db.add_frame(nm_responde)

        sync = canmatrix.canmatrix.Frame(name="SYNC", size=0, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0x80), transmitters=[plc_name])
        db.add_frame(sync)

        emcy = canmatrix.canmatrix.Frame(name="EMCY", size=8, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0x80+node_id), transmitters=[node_name])
        emcy.add_signal(canmatrix.canmatrix.Signal(name="EMCY_Error_Code", size=16, start_bit=0, receivers=[plc_name]))
        emcy.add_signal(canmatrix.canmatrix.Signal(name="E_Reg", size=8, start_bit=16, receivers=[plc_name]))
        emcy.add_signal(canmatrix.canmatrix.Signal(name="E_Number", size=8, start_bit=24, receivers=[plc_name]))
        db.add_frame(emcy)

    sdo_down = canmatrix.canmatrix.Frame(name="SDO_receive", size=8, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0x600+node_id), transmitters=[node_name])
    sig_cmd = canmatrix.canmatrix.Signal(name="CCS", size=3, start_bit=5, receivers=[plc_name], is_signed=False)
    sig_cmd.is_multiplexer = True
    sdo_down.is_complex_multiplexed = True
    sig_cmd.multiplex = "Multiplexor"
    sdo_down.add_signal(sig_cmd)
    index = canmatrix.canmatrix.Signal(name="IDX", size=24, start_bit=8, receivers=[plc_name])
    index.multiplex = "Multiplexor"
    index.is_multiplexer = True
    index.mux_val = 1
    index.mux_val_grp.append([ 2, 2])
    index.muxer_for_signal = "CCS"
    sdo_down.add_signal(index)
    db.add_frame(sdo_down)

    sdo_up = canmatrix.canmatrix.Frame(name="SDO_transmit", size=8, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0x580+node_id), transmitters=[plc_name])
    sig_cmd = canmatrix.canmatrix.Signal(name="SCS", size=3, start_bit=5, is_signed=False)
    sig_cmd.is_multiplexer = True
    sdo_up.is_complex_multiplexed = True
    sig_cmd.multiplex = "Multiplexor"
    sdo_up.add_signal(sig_cmd)

    index = canmatrix.canmatrix.Signal(name="IDX", size=24, start_bit=8)
    index.multiplex = "Multiplexor"
    index.is_multiplexer = True
    index.mux_val = 2
    index.mux_val_grp.append([ 2, 2])
    index.muxer_for_signal = "SCS"
    sdo_up.add_signal(index)
    db.add_frame(sdo_up)


    for obj in od.values():
        if isinstance(obj, canopen.objectdictionary.ODVariable):
            subindex = 0
            combined_value = int(f"{subindex:02X}{obj.index:04X}", 16)
            signal_name = name_cleanup(obj.name)
            size = get_bit_length(obj.data_type)
            if size == 0:
                logger.info("Ignoring " + signal_name + " size 0")
                continue
            new_sig = canmatrix.canmatrix.Signal(name=signal_name, size=size, start_bit=32, receivers=[plc_name])
            datatype_name = get_data_type_name(obj.data_type)
            if "UNSIGNED" in datatype_name:
                new_sig.is_signed = False
            new_sig.mux_val = combined_value
            new_sig.mux_val_grp.append([ combined_value, combined_value])
            new_sig.muxer_for_signal = "IDX"
            sdo_down.add_signal(new_sig)
            up_sig = copy.deepcopy(new_sig)
            up_sig.muxer_for_signal = "IDX"

            up_sig.receivers = []
            sdo_up.add_signal(up_sig)
        elif isinstance(obj, canopen.objectdictionary.ODRecord):
            members = []
            for subobj in obj.values():
                combined_value = int(f"{subobj.subindex:02X}{obj.index:04X}", 16)
                signal_name = name_cleanup(subobj.name)
                size = get_bit_length(subobj.data_type)
                if size == 0:
                    logger.info("Ignoring " + signal_name + " size 0")
                    continue

                new_sig = canmatrix.canmatrix.Signal(name=signal_name, size=size, start_bit=32, receivers=[plc_name])
                datatype_name = get_data_type_name(subobj.data_type)
                if "UNSIGNED" in datatype_name:
                    new_sig.is_signed = False
                new_sig.mux_val = combined_value
                new_sig.mux_val_grp.append([ combined_value, combined_value])
                new_sig.muxer_for_signal = "IDX"
                sdo_down.add_signal(new_sig)
                up_sig = copy.deepcopy(new_sig)
                up_sig.muxer_for_signal = "IDX"

                up_sig.receivers = []
                sdo_up.add_signal(up_sig)
            if len(members) > 0:
                sdo_down.add_signal_group("SG_R_" + name_cleanup(obj.name), signal_group_counter, members)
                signal_group_counter += 1

        elif isinstance(obj, canopen.objectdictionary.ODArray):
            members = []
            for subobj in obj.values():
                combined_value = int(f"{subobj.subindex:02X}{obj.index:04X}", 16)
                signal_name = name_cleanup(subobj.name)
                size = get_bit_length(subobj.data_type)
                if size == 0:
                    logger.info("Ignoring " + signal_name + " size 0")
                    continue

                new_sig = canmatrix.canmatrix.Signal(name=signal_name, size=size, start_bit=32, receivers=[plc_name])
                datatype_name = get_data_type_name(subobj.data_type)
                if "UNSIGNED" in datatype_name:
                    new_sig.is_signed = False
                new_sig.mux_val = combined_value
                new_sig.mux_val_grp.append([ combined_value, combined_value])
                new_sig.muxer_for_signal = "IDX"
                sdo_down.add_signal(new_sig)
                members.append(signal_name)
                up_sig = copy.deepcopy(new_sig)
                up_sig.muxer_for_signal = "IDX"
                up_sig.receivers = []
                sdo_up.add_signal(up_sig)
            if len(members) > 0:
                sdo_down.add_signal_group("SG_A_" + name_cleanup(obj.name), signal_group_counter, members)
                signal_group_counter += 1


    for start_index, rx_tx_config in {0x1400 : {"transmitter": [], "receiver": [node_name]}, 0x1800: {"transmitter": [node_name], "receiver": []}}.items():       
        for comm_index in range(start_index, start_index + 0x8):
            map_index = comm_index + 0x200
            if comm_index not in od or map_index not in od:
                continue

            # Retrieve the COB-ID
            comm_param = od[comm_index] #od.get(comm_index)
            cob_id_entry = comm_param.get(1) if comm_param else None
            if not cob_id_entry or cob_id_entry.default is None:
            # print(f"  Warning: No valid COB-ID found for {pdo_type} PDO at index 0x{comm_index:04X}. Skipping.")
                continue
            cob_id = cob_id_entry.default & 0x7FF
            pdo_name = name_cleanup(od[comm_index].name)
            frame = canmatrix.canmatrix.Frame(name=pdo_name, transmitters=rx_tx_config["transmitter"])
            frame_id = cob_id
            frame.arbitration_id = canmatrix.ArbitrationId(id=frame_id)
            db.add_frame(frame)
            mapping_param = od.get(map_index)
            if not mapping_param:
    #            print(f"  Warning: No mapping parameter found for {pdo_type} PDO at index 0x{map_index:04X}.")
                continue
            num_entries = mapping_param[0].default if 0 in mapping_param else 0
            current_bit_start = 0
            for subindex in range(1, num_entries + 1):
                mapping_entry = mapping_param.get(subindex)
                if not mapping_entry or mapping_entry.default is None:
                    #print(f"  Warning: Subindex {subindex} missing for mapping parameter at 0x{map_index:04X}.")
                    continue

                # Decode the mapping entry
                mapping_value = mapping_entry.default
                obj_index = (mapping_value >> 16) & 0xFFFF
                obj_subindex = (mapping_value >> 8) & 0xFF
                bit_length = mapping_value & 0xFF

                # Fetch the mapped object
                mapped_obj = od.get_variable(obj_index, obj_subindex)
                if not mapped_obj:
                    #print(f"  Warning: Could not find object at Index: 0x{obj_index:04X}, Subindex: {obj_subindex}.")
                    current_bit_start += bit_length
                    continue
                signal_name = name_cleanup(mapped_obj.name)
                new_sig = canmatrix.Signal(signal_name, size=bit_length, start_bit=current_bit_start)
                datatype_name = get_data_type_name(mapped_obj.data_type)
                if "UNSIGNED" in datatype_name:
                    new_sig.is_signed = False
                new_sig.factor = mapped_obj.factor
                if mapped_obj.min is not None:
                    new_sig.min = mapped_obj.min
                    new_sig.offset = mapped_obj.min
                if mapped_obj.max is not None:
                    new_sig.max = mapped_obj.max
                new_sig.receivers = rx_tx_config["receiver"]
                frame.add_signal(new_sig)
                current_bit_start += bit_length
                frame.size =  math.ceil(current_bit_start/8)

    db.update_ecu_list()   
    for ecu in db.ecus:
        db.rename_ecu(ecu.name, name_cleanup(ecu.name))
    return db
