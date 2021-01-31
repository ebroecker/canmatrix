from lxml import etree
import canmatrix.formats


class OdxReader:
    def __init__(self):
        self.tree = None
        self.root = None
        self.ns = None
        self.nsp = None

    def open(self, file):
        self.tree = etree.parse(file)
        self.root = self.tree.getroot()
        self.ns = "{" + self.tree.xpath('namespace-uri(.)') + "}"  # type: str
        self.nsp = self.tree.xpath('namespace-uri(.)')
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


def read_param(eo : OdxReader, param):
    short_name = eo.get_short_name(param)
    byte_pos = eo.find("BYTE-POSITION", param)
    coded_value = eo.find("CODED-VALUE", param)
    bit_length = eo.find("BIT-LENGTH", param)
    try:
        value = int(coded_value.text)
        bit_length = int(bit_length.text)
        byte_pos = int(byte_pos.text)
        return (value, bit_length, byte_pos, short_name)
    except:
        return (0,0,0, short_name)


def get_odx_info(eo: OdxReader, element_type):
    service_id = {}
    for request in eo.findall(element_type):
        short_name = eo.get_short_name(request)
        current_mux1 = 0
        current_mux2 = 0
        for param in eo.findall("PARAM", request):
            (value, bit_length, byte_pos, name) = read_param(eo, param)
            if byte_pos == 0 and bit_length == 8:
                current_mux1 = value
                if value not in service_id:
                    service_id[value] = {}
            if byte_pos == 1:
                service_id[current_mux1][value] = {"bit_length": bit_length, "name": short_name}
                current_mux2 = value
            if byte_pos == 2:
                service_id[current_mux1][current_mux2][value] = {"bit_length": bit_length, "name": short_name}
#            print(" {:02x}".format(value), end='')
#        print(" ")
    return service_id


def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    if 'odxRxId' in options:
        rx_can_id = options["odxRxId"]
    else:
        rx_can_id = 0x2
    if 'odxTxId' in options:
        tx_can_id = options["odxTxId"]
    else:
        tx_can_id = 0x1

    db = canmatrix.canmatrix.CanMatrix()
    eo = OdxReader()
    eo.open(f)

    ### request
    info_struct = get_odx_info(eo, "REQUEST")
    tx_frame = canmatrix.canmatrix.Frame(arbitration_id=canmatrix.arbitration_id_converter(tx_can_id),
                                         name="Diag_Reqest", size=8)
    service_id = canmatrix.canmatrix.Signal("service_id", start_bit=0, size=8)
    tx_frame.add_signal(service_id)
    service_id.is_multiplexer = True

    for mux_val in info_struct:
        request_id_signal = canmatrix.canmatrix.Signal("service_{:02x}".format(mux_val), start_bit=8, multiplex=mux_val)
        for value in info_struct[mux_val]:
            request_id_signal.add_values(value, info_struct[mux_val][value]["name"])
            request_id_signal.size = info_struct[mux_val][value]["bit_length"]
        tx_frame.add_signal(request_id_signal)
    db.add_frame(tx_frame)


    ### response
    info_struct = get_odx_info(eo, "POS-RESPONSE")
    info_struct.update(get_odx_info(eo, "NEG-RESPONSE"))

    tx_frame = canmatrix.canmatrix.Frame(arbitration_id=canmatrix.arbitration_id_converter(rx_can_id),
                                         name="Diag_Response", size=8)
    service_id = canmatrix.canmatrix.Signal("service_id", start_bit=0, size=8)
    tx_frame.add_signal(service_id)
    service_id.is_multiplexer = True
    for mux_val in info_struct:
        if mux_val != 0x7f:
            request_id_signal = canmatrix.canmatrix.Signal("service_{:02x}".format(mux_val-0x40), start_bit=8,
                                                       multiplex=mux_val)
        else:
            request_id_signal = canmatrix.canmatrix.Signal("service_{:02x}".format(mux_val), start_bit=8,
                                                       multiplex=mux_val)

        for value in info_struct[mux_val]:
            request_id_signal.add_values(value, info_struct[mux_val][value]["name"])
            request_id_signal.size = info_struct[mux_val][value]["bit_length"]
        tx_frame.add_signal(request_id_signal)
    db.add_frame(tx_frame)

    return db
