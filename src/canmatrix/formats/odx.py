from __future__ import print_function

from lxml import etree
import canmatrix.formats
import decimal


class OdxReader:
    def __init__(self):
        self.tree = None
        self.root = None
        self.ns = None
        self.nsp = None
        self.id_links = {}

    def open(self, file):
        self.tree = etree.parse(file)
        self.root = self.tree.getroot()
        self.ns = "{" + self.tree.xpath('namespace-uri(.)') + "}"  # type: str
        self.nsp = self.tree.xpath('namespace-uri(.)')

        for element in self.findall("*"):
            if "ID" in element.attrib:
                self.id_links[element.attrib["ID"]] = element

        return

    def findall(self, xpath, root=None):
        if root is None:
            root = self.root
        return root.findall('.//' + self.ns + xpath)

    def find(self, xpath, root=None):
        if root is None:
            root = self.root
        return root.find('.//' + self.ns + xpath)

    def get_short_name(self, element):
        short_name = element.find(self.ns + "SHORT-NAME")
        return short_name.text


def read_param(eo, param, start_byte_pos=0):
    return_data = {}
    short_name = eo.get_short_name(param)
    byte_pos = eo.find("BYTE-POSITION", param)
    bit_pos = eo.find("BIT-POSITION", param)
    coded_value = eo.find("CODED-VALUE", param)
    bit_length = eo.find("BIT-LENGTH", param)
    dop_ref = eo.find("DOP-REF", param)
    if dop_ref is not None and eo.id_links[dop_ref.attrib["ID-REF"]].tag != "DATA-OBJECT-PROP":
        # TODO
        struct_ref = dop_ref.attrib["ID-REF"]
        target = eo.id_links[struct_ref]


        if target.tag == "STRUCTURE":
            for param in eo.findall("PARAM", target):
                print(byte_pos.text, end=" ")
                return_data.update(read_param(eo, param, start_byte_pos+int(byte_pos.text)))
            print()
 #       else:
 #           print("-")
#        print(eo.id_links[struct_ref])

    try:
        value = int(coded_value.text)
    except:
        value = None
    try:
        bit_length = int(bit_length.text)
    except:
        bit_length = 8

    byte_pos = int(byte_pos.text)
    try:
        bit_pos = int(bit_pos.text)
    except:
        bit_pos = 0

    return_data.update({short_name: [value, bit_length, byte_pos, bit_pos]})
    return return_data


def find_param(eo, request, param_type):
    for param in eo.findall("PARAM", request):
        if param.attrib["SEMANTIC"] == param_type:
            return param
    return None

def decode_compumethod(eo, compu_method, category):
    compu_info = {}
    if category == "TEXTTABLE":
        compu_info["type"] = "TEXTTABLE"
        compu_info["table"] = {}
        for compu_scale in eo.findall("COMPU-SCALE", compu_method):
            vt = eo.find("COMPU-CONST/VT", compu_scale)
            ll = eo.find("LOWER-LIMIT", compu_scale)
            compu_info["table"][ll.text] = vt.text
    elif category =="LINEAR":
        # num0 + num1*x/denum
        compu_info["type"] = "LINEAR"
        numerators = eo.findall("COMPU-NUMERATOR/V", compu_method)
        offset = numerators[0].text
        factor = numerators[1].text

        denominator = eo.find("COMPU-DENOMINATOR/V", compu_method)
        if denominator is not None:
            teiler = denominator.text
        else:
            teiler = 1

        compu_info["offset"] = offset
        compu_info["teiler"] = teiler
        compu_info["factor"] = factor

    elif category == "IDENTICAL":
        compu_info["type"] = "IDENTICAL"

    return compu_info


def get_struct(eo, struct_name, offset_bit=0):
    struct = eo.id_links[struct_name]

    byte_size = eo.find("BYTE-SIZE", struct)
    bit_size = eo.find("BIT-SIZE", struct)
    name = eo.get_short_name(struct)
    data_dict = {"name": name, "_members": {}}
    if byte_size is not None:
        data_dict["bit_size"] = int(byte_size.text)*8
    if bit_size is not None:
        data_dict["bit_size"] = int(bit_size.text)

    for param in eo.findall("PARAM", struct):
        ref = eo.find("DOP-REF", param)
        param_name = eo.get_short_name(param)
        byte_pos = eo.find("BYTE-POSITION", param)
        bit_pos = eo.find("BIT-POSITION", param)
        start_bit = int(byte_pos.text)*8 + offset_bit
        if bit_pos is not None:
            start_bit += int(bit_pos.text)
        data_dict["_members"][param_name] = {"bit_pos": start_bit}
        data_dict["_members"][param_name]["name"] = param_name

        if ref is not None:
            if eo.id_links[ref.attrib["ID-REF"]].tag == "DATA-OBJECT-PROP":
                data_prop = eo.id_links[ref.attrib["ID-REF"]]
                bit_len = eo.find("BIT-LENGTH", data_prop)
                data_dict["_members"][param_name]["bit_size"] = int(bit_len.text)
                compu_method_cat = eo.find("COMPU-METHOD/CATEGORY", data_prop)
                if compu_method_cat is not None:
                    decoded_compu = decode_compumethod(eo, eo.find("COMPU-METHOD", data_prop), compu_method_cat.text)
                    data_dict["_members"][param_name]["compu_method"] = decoded_compu
                unit_ref = eo.find("UNIT-REF", data_prop)
                if unit_ref is not None:
                    unit_element = eo.id_links[unit_ref.attrib["ID-REF"]]
                    display_name_element = eo.find("DISPLAY-NAME", unit_element)
                    data_dict["_members"][param_name]["unit"] = display_name_element.text
                # ignore type for now...
            else:
                data_dict["_members"][param_name] = get_struct(eo, ref.attrib["ID-REF"], start_bit)
    return data_dict


def get_odx_info(eo, element_type):
    did_infos = {}
    for request in eo.findall(element_type):
        short_name = eo.get_short_name(request)
        service_id_param = find_param(eo, request, "SERVICE-ID")
        if service_id_param == None:
            continue

        service_id_value = eo.find("CODED-VALUE", service_id_param)
        service_id = int(service_id_value.text)

        if service_id != 0x62:
            continue

        id_param = find_param(eo, request, "ID")
        if id_param == None:
            continue
        did_value = eo.find("CODED-VALUE", id_param)
        did = int(did_value.text)


        data = find_param(eo, request, "DATA")
        data_type = eo.find("DOP-REF", data)
        structure = eo.id_links[data_type.attrib["ID-REF"]]
        if structure.tag != "STRUCTURE":
            continue
        did_infos[did] = get_struct(eo, structure.attrib["ID"])
    return did_infos


def flatten_did_info(did_info):
    flattened_info = {}
    if "_members" in did_info:
        flattened_info.update(flatten_did_info(did_info["_members"]))
    elif "bit_pos" in did_info and "name" in did_info:
        if "compu_method" in did_info:
            pass
        return {did_info["name"]: did_info}
        #todo
    else:
        for var in did_info:
            flattened_info.update(flatten_did_info(did_info[var]))
    return flattened_info


def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    if 'odxRxId' in options:
        rx_can_id = options["odxRxId"]
    else:
        rx_can_id = 0x2
    if 'odxTxId' in options:
        tx_can_id = options["odxTxId"]
    else:
        tx_can_id = 0x1

    decode_service = 0x22

    db = canmatrix.canmatrix.CanMatrix()
    eo = OdxReader()
    eo.open(f)
# 22, 2E write by id, 2f, InputOutputControlByIdent, 31 Routine Control,
    # functional_canid_container = eo.root.xpath("//COMPARAM-REF[@ID-REF='COMPARAM-SPEC.UDS_CPS.COMPARAM.FunctionalRequestCANID']")
    ### request
    pyhs_canid_container = eo.root.xpath("//COMPARAM-REF[@ID-REF='COMPARAM-SPEC.UDS_CPS.COMPARAM.PhysicalRequestCANID']")
    if len(pyhs_canid_container) > 0:
        value = eo.find("VALUE", pyhs_canid_container[0])
        if value is not None:
            tx_can_id = int(value.text, 16)

    info_struct = {} # get_odx_info(eo, "REQUEST")
    tx_frame = canmatrix.canmatrix.Frame(arbitration_id=canmatrix.arbitration_id_converter(tx_can_id),
                                         name="Diag_Reqest", size=8)

    if decode_service == 0:
        service_id = canmatrix.canmatrix.Signal("service_id", start_bit=8, size=8)
        tx_frame.add_signal(service_id)
        service_id.multiplex = 'Multiplexor'
    else:
#        info_struct = info_struct[decode_service]
        service_id = canmatrix.canmatrix.Signal("service_{:x}_muxer".format(decode_service), start_bit=8, size=24)
        tx_frame.add_signal(service_id)
        service_id.multiplex = 'Multiplexor'
        service_id.is_signed = False


    for mux_val in info_struct:
        request_id_signal = canmatrix.canmatrix.Signal(info_struct[mux_val]["name"], start_bit=32, multiplex=mux_val)
        request_id_signal.size = info_struct[mux_val]["bit_length"]
   #     for value in info_struct[mux_val]:
   #         request_id_signal.add_values(value, info_struct[mux_val][value]["name"])
   #         request_id_signal.size = info_struct[mux_val][value]["bit_length"]
        if request_id_signal.size > 0:
            tx_frame.add_signal(request_id_signal)

    db.add_frame(tx_frame)


    ### response
    info_struct = get_odx_info(eo, "POS-RESPONSE" )
#    info_struct.update(get_odx_info(eo, "NEG-RESPONSE"))

    pyhs_canid_container = eo.root.xpath("//COMPARAM-REF[@ID-REF='COMPARAM-SPEC.UDS_CPS.COMPARAM.PhysicalResponseCANID']")
    if len(pyhs_canid_container) > 0:
        value = eo.find("VALUE", pyhs_canid_container[0])
        if value is not None:
            rx_can_id = int(value.text, 16)
    tx_frame = canmatrix.canmatrix.Frame(arbitration_id=canmatrix.arbitration_id_converter(rx_can_id),
                                         name="Diag_Response", size=8)

    tp_info = canmatrix.canmatrix.Signal("tp_length", start_bit=0, size=8)
    tx_frame.add_signal(tp_info)
    service_id = canmatrix.canmatrix.Signal("service_{:x}_muxer".format(decode_service+0x40), start_bit=8, size=24)
    tx_frame.add_signal(service_id)
    service_id.multiplex = 'Multiplexor'
    service_id.is_signed = False

    for mux_val in info_struct:
        service_id.add_values(mux_val, info_struct[mux_val]["name"])
        did_info = info_struct[mux_val]
        did_vars = flatten_did_info(did_info)
        for var in did_vars:
            new_signal = canmatrix.canmatrix.Signal(var, multiplex=mux_val)
            if "bit_size" in did_vars[var]:
                new_signal.size = did_vars[var]["bit_size"]
            else:
                new_signal.size = 1
            new_signal.start_bit = did_vars[var]["bit_pos"] + 32
            new_signal.is_signed = False
            if "compu_method" in did_vars[var]:
                if did_vars[var]["compu_method"]["type"] == "LINEAR":
                    offset = decimal.Decimal(did_vars[var]["compu_method"]["offset"])
                    factor = decimal.Decimal(did_vars[var]["compu_method"]["factor"])
                    teiler = decimal.Decimal(did_vars[var]["compu_method"]["teiler"])
                    new_signal.factor = factor / teiler
                    new_signal.offset = offset / teiler
                elif did_vars[var]["compu_method"]["type"] == "TEXTTABLE":
                    for value, value_name in did_vars[var]["compu_method"]["table"].items():
                        new_signal.add_values(int(value), value_name)
            if "unit" in did_vars[var]:
                new_signal.unit = did_vars[var]["unit"]

            tx_frame.add_signal(new_signal)

    db.add_frame(tx_frame)

    return db
