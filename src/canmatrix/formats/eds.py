import logging
import canmatrix
import typing
import canopen.objectdictionary.eds
import canopen.objectdictionary.datatypes
import codecs


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


def get_signals(parent_object, signal_receiver):
    signals = []
    position = 0
    for sub in range(1, len(parent_object)):
        name = parent_object[sub].name
        size = datatype_mapping[parent_object[sub].data_type][1]
        factor = parent_object[sub].factor
        unsigned = "UNSIGNED" in datatype_mapping[parent_object[sub].data_type][0]
        signal = canmatrix.Signal(name = name, receivers=[signal_receiver], size=size, start_bit = position, factor=factor, is_signed = not unsigned)
        if parent_object[sub].min is not None:
            signal.offset = parent_object[sub].min
        position += size
        signals.append(signal)
    return signals


def get_bit_length(data_type_code):
    return  datatype_mapping[data_type_code][1]
#def get_data_type_name(data_type_code):
#    return  datatype_mapping[data_type_code][0]
    
def format_index(index, subindex):
    return f"Index: 0x{index:04X}{subindex:02X}"

def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    eds_import_encoding = options.get("edsImportEncoding", 'iso-8859-1')
    node_id = options.get("eds_node_id", 1)
    generic = options.get("generic", False)
    fp = codecs.getreader(eds_import_encoding)(f)
    od = canopen.objectdictionary.eds.import_eds(fp, node_id)
    db = canmatrix.CanMatrix()

    node_name = od.device_information.product_name
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

    sdo_down = canmatrix.canmatrix.Frame(name="SDO_download", size=8, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0x600+node_id), transmitters=[node_name])
    sig_cmd = canmatrix.canmatrix.Signal(name="sdo_down_CMD", size=5, start_bit=3, receivers=[plc_name])
    sig_cmd.is_multiplexer = True
    sdo_down.is_complex_multiplexed = True
    sig_cmd.multiplex = "Multiplexor"
    sdo_down.add_signal(sig_cmd)
    index = canmatrix.canmatrix.Signal(name="sdo_down_IDX", size=24, start_bit=8, receivers=[plc_name])
    index.multiplex = "Multiplexor"
    index.is_multiplexer = True
    index.mux_val = 2
    index.mux_val_grp.append([ 2, 2])
    index.muxer_for_signal = "sdo_down_CMD"
    sdo_down.add_signal(index)

#    sdo_down.add_signal(canmatrix.canmatrix.Signal(name="sdo_down_SUBIDX", size=8, start_bit=24, receivers=[plc_name]))

#    bla = canmatrix.canmatrix.Signal(name="test_it", size=8, start_bit=32, receivers=[plc_name])
#    bla.muxer_for_signal = "sdo_down_IDX"

    #sig_cmd.add_values(0x2f, "8_bytes")
    #sdo_down.add_signal(canmatrix.canmatrix.Signal(name="data16", size=16, start_bit=32, receivers=[plc_name], multiplex=0x2b))
    #sig_cmd.add_values(0x2b, "16_bytes")
    #sdo_down.add_signal(canmatrix.canmatrix.Signal(name="data24", size=24, start_bit=32, receivers=[plc_name], multiplex=0x27))
    #sig_cmd.add_values(0x27, "3_bytes")
    #sdo_down.add_signal(canmatrix.canmatrix.Signal(name="data32", size=32, start_bit=32, receivers=[plc_name], multiplex=0x23))
    #sig_cmd.add_values(0x23, "4_bytes")
    #sig_cmd.add_values(0x40, "upload_request")
    db.add_frame(sdo_down)

    sdo_up = canmatrix.canmatrix.Frame(name="SDO_upload", size=8, arbitration_id=canmatrix.canmatrix.ArbitrationId(id=0x580+node_id), transmitters=[plc_name])
    sig_cmd = canmatrix.canmatrix.Signal(name="sdo_state", size=8, start_bit=0, receivers=[node_name])
    sig_cmd.is_multiplexer = True
    sig_cmd.multiplex = "Multiplexor"
    sdo_up.add_signal(sig_cmd)
    sdo_up.add_signal(canmatrix.canmatrix.Signal(name="sdo_uo_IDX", size=16, start_bit=8, receivers=[node_name]))
    sdo_up.add_signal(canmatrix.canmatrix.Signal(name="sdo_up_SUBIDX", size=8, start_bit=24, receivers=[node_name]))
    sdo_up.add_signal(canmatrix.canmatrix.Signal(name="error_code", size=32, start_bit=32, receivers=[node_name], multiplex=0x80))
    sig_cmd.add_values(0x80, "upload_error")

    sdo_up.add_signal(canmatrix.canmatrix.Signal(name="data8", size=8, start_bit=32, receivers=[plc_name], multiplex=0x4f))
    sig_cmd.add_values(0x2f, "8_bytes")
    sdo_up.add_signal(canmatrix.canmatrix.Signal(name="data16", size=16, start_bit=32, receivers=[plc_name], multiplex=0x4b))
    sig_cmd.add_values(0x2b, "16_bytes")
    sdo_up.add_signal(canmatrix.canmatrix.Signal(name="data24", size=24, start_bit=32, receivers=[plc_name], multiplex=0x47))
    sig_cmd.add_values(0x27, "3_bytes")
   # sdo_down.add_signal(canmatrix.canmatrix.Signal(name="data32", size=32, start_bit=32, receivers=[plc_name], multiplex=0x43))
    sig_cmd.add_values(0x23, "4_bytes")
    db.add_frame(sdo_up)

    for obj in od.values():
        if isinstance(obj, canopen.objectdictionary.ODVariable):
            subindex = 0
            combined_value = int(f"{subindex:02X}{obj.index:04X}", 16)
            new_sig = canmatrix.canmatrix.Signal(name=obj.name.replace(' ', '_'), size=get_bit_length(obj.data_type), start_bit=32, receivers=[plc_name])

            new_sig.mux_val = combined_value
            new_sig.mux_val_grp.append([ combined_value, combined_value])
            new_sig.muxer_for_signal = "sdo_down_IDX"
            sdo_down.add_signal(new_sig)


    # RX Can-Ids ...
    for index in range(0x1400, 0x1408):
        if index in od:
            # store canid in object...
            od[index+0x200].canid = od[index][1].default

    ##RX PDOs
    for index in range(0x1600, 0x1608):   
        if index in od:
            pdo_name = od[index].name.replace(" ", "_")
            frame = canmatrix.canmatrix.Frame(name=pdo_name, transmitters=[plc_name])
            db.add_frame(frame)
            frame_id = od[index].canid
            frame.arbitration_id = canmatrix.ArbitrationId(id=frame_id)
            frame.size = 8
            signals = get_signals(od[index], node_name)
            for sig in signals:
                frame.add_signal(sig)

    # RT Can-Ids ...
    for index in range(0x1800, 0x1808):
        if index in od:
            # store canid in object...
            od[index+0x200].canid = od[index][1].default & 0x7FF

    #TX
    for index in range(0x1A00, 0x1A08):   
        if index in od:
            pdo_name = od[index].name.replace(" ", "_")
            frame = canmatrix.canmatrix.Frame(name=pdo_name, transmitters=[node_name])
            db.add_frame(frame)
            frame_id = od[index].canid
            frame.arbitration_id = canmatrix.ArbitrationId(id=frame_id)
            frame.size = 8
            signals = get_signals(od[index], plc_name)
            for sig in signals:
                frame.add_signal(sig)

    db.update_ecu_list()   
    for ecu in db.ecus:
        if "-" in ecu.name:
            db.rename_ecu(ecu.name, ecu.name.replace("-","_").replace(" ", "_"))
        else:
            db.rename_ecu(ecu.name, ecu.name.replace(" ", "_"))

    return db
