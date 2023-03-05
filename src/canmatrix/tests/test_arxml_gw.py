import canmatrix.formats.arxml
import textwrap
import io


def test_pdu_gateway():
    arxml = io.BytesIO(textwrap.dedent(u'''\
    <AUTOSAR xmlns="http://autosar.org/schema/r4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://autosar.org/schema/r4.0 autosar_4-3-0.xsd">

    <AR-PACKAGE>
      <SHORT-NAME>Cluster</SHORT-NAME>
      <ELEMENTS>
        <CAN-CLUSTER>
          <SHORT-NAME>someCluster</SHORT-NAME>
          <CAN-CLUSTER-VARIANTS>
            <CAN-CLUSTER-CONDITIONAL>
              <PHYSICAL-CHANNELS>
                <CAN-PHYSICAL-CHANNEL>
                  <SHORT-NAME>CHNL</SHORT-NAME>
                   <FRAME-TRIGGERINGS>
                    <CAN-FRAME-TRIGGERING>
                      <SHORT-NAME>SomeFrameTriggering</SHORT-NAME>
                      <PDU-TRIGGERINGS>
                        <PDU-TRIGGERING-REF-CONDITIONAL>
                          <PDU-TRIGGERING-REF DEST="PDU-TRIGGERING">/Cluster/someCluster/CHNL/somePDUTriggering</PDU-TRIGGERING-REF>
                        </PDU-TRIGGERING-REF-CONDITIONAL>
                      </PDU-TRIGGERINGS>
                    </CAN-FRAME-TRIGGERING>
                   </FRAME-TRIGGERINGS>
                   <PDU-TRIGGERINGS>
                    <PDU-TRIGGERING>
                      <SHORT-NAME>somePduTriggering</SHORT-NAME>
                      <I-PDU-REF DEST="NM-PDU">/PDU/somePdu</I-PDU-REF>
                    </PDU-TRIGGERING>
                   </PDU-TRIGGERINGS>
                </CAN-PHYSICAL-CHANNEL>
              </PHYSICAL-CHANNELS>
            </CAN-CLUSTER-CONDITIONAL>
          </CAN-CLUSTER-VARIANTS>
        </CAN-CLUSTER>

        <CAN-CLUSTER>
          <SHORT-NAME>someOtherCluster</SHORT-NAME>
          <CAN-CLUSTER-VARIANTS>
            <CAN-CLUSTER-CONDITIONAL>
              <PHYSICAL-CHANNELS>
                <CAN-PHYSICAL-CHANNEL>
                  <SHORT-NAME>CHNL</SHORT-NAME>
                   <FRAME-TRIGGERINGS>
                    <CAN-FRAME-TRIGGERING>
                      <SHORT-NAME>SomeOtherFrameTriggering</SHORT-NAME>
                      <PDU-TRIGGERINGS>
                        <PDU-TRIGGERING-REF-CONDITIONAL>
                          <PDU-TRIGGERING-REF DEST="PDU-TRIGGERING">/Cluster/someCluster/CHNL/someOtherPDUTrigering</PDU-TRIGGERING-REF>
                        </PDU-TRIGGERING-REF-CONDITIONAL>
                      </PDU-TRIGGERINGS>
                    </CAN-FRAME-TRIGGERING>
                   </FRAME-TRIGGERINGS>
                   <PDU-TRIGGERINGS>
                    <PDU-TRIGGERING>
                      <SHORT-NAME>someOtherPduTriggering</SHORT-NAME>
                      <I-PDU-REF DEST="NM-PDU">/PDU/someOtherPdu</I-PDU-REF>
                    </PDU-TRIGGERING>
                   </PDU-TRIGGERINGS>
                </CAN-PHYSICAL-CHANNEL>
              </PHYSICAL-CHANNELS>
            </CAN-CLUSTER-CONDITIONAL>
          </CAN-CLUSTER-VARIANTS>
        </CAN-CLUSTER>


      </ELEMENTS>
    </AR-PACKAGE>
    <AR-PACKAGE>
        <SHORT-NAME>Gateway</SHORT-NAME>
        <ELEMENTS>
            <GATEWAY>
              <SHORT-NAME>someECU</SHORT-NAME>
              <ECU-REF DEST="ECU-INSTANCE">/ECU/someECU</ECU-REF>
              <I-PDU-MAPPINGS>
                <I-PDU-MAPPING>
                <SOURCE-I-PDU-REF DEST="PDU-TRIGGERING">/Cluster/someCluster/CHNL/somePduTriggering</SOURCE-I-PDU-REF>
                <TARGET-I-PDU>
                    <TARGET-I-PDU-REF DEST="PDU-TRIGGERING">/Cluster/someOtherCluster/CHNL/someOtherPduTriggering</TARGET-I-PDU-REF>
                </TARGET-I-PDU>
                </I-PDU-MAPPING>
              </I-PDU-MAPPINGS>
            </GATEWAY>
        </ELEMENTS>
    </AR-PACKAGE>
    </AUTOSAR>''').encode('utf-8'))

    cluster = canmatrix.formats.arxml.load(arxml)

    assert cluster.get_routing_info("someOtherPdu")["target"][0] == "/PDU/somePdu"
    assert cluster.get_routing_info("/PDU/somePdu", strict_search=True)["source"][0] == "/PDU/someOtherPdu"
