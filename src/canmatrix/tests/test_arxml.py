# -*- coding: utf-8 -*-
import canmatrix.formats.arxml
import pathlib2
import io
import textwrap

def test_ecu_extract():
    here = pathlib2.Path(__file__).parent
    
    db = canmatrix.formats.arxml.load(str(here / "MyECU.ecuc.arxml"))['']
    assert db.frames is not None
    assert len(db.frames) == 2
    assert len(db.frames[0].signals) == 3
    assert len(db.frames[1].signals) == 1


def test_get_signals_from_container_i_pdu():
    arxml = io.BytesIO(textwrap.dedent(u'''\
    <ARXML>
    <AR-PACKAGE>
        <SHORT-NAME>B</SHORT-NAME>
        <CAN-FRAME>
          <SHORT-NAME>CAN_FRAME_FD</SHORT-NAME>
          <FRAME-LENGTH>64</FRAME-LENGTH>
            <PDU-TO-FRAME-MAPPINGS>
                <PDU-TO-FRAME-MAPPING>
                  <SHORT-NAME>CAN_FRAME_FD_PDU_MAPPING</SHORT-NAME>
                  <PACKING-BYTE-ORDER>MOST-SIGNIFICANT-BYTE-LAST</PACKING-BYTE-ORDER>
                  <PDU-REF DEST="SIGNAL-I-PDU">/A/Frame_FD_CONTAINER</PDU-REF>
                  <START-POSITION>0</START-POSITION>
                </PDU-TO-FRAME-MAPPING>
              </PDU-TO-FRAME-MAPPINGS>
        </CAN-FRAME>
        <I-SIGNAL-I-PDU>
            <SHORT-NAME>PDU1</SHORT-NAME>            
            <SOME>
                <TRANSMISSION-MODE-CONDITION>
                    <I-SIGNAL-IN-I-PDU-REF>/A/SignalIPDUAssignment1</I-SIGNAL-IN-I-PDU-REF>
                </TRANSMISSION-MODE-CONDITION>
            </SOME>
        </I-SIGNAL-I-PDU>
        <I-SIGNAL-I-PDU>
            <SHORT-NAME>PDU2</SHORT-NAME>            
            <SOME>
                <TRANSMISSION-MODE-CONDITION>
                    <I-SIGNAL-IN-I-PDU-REF>/A/SignalIPDUAssignment2</I-SIGNAL-IN-I-PDU-REF>
                </TRANSMISSION-MODE-CONDITION>
            </SOME>
        </I-SIGNAL-I-PDU>
        
        <SYSTEM-SIGNAL>
          <SHORT-NAME>Enable_command</SHORT-NAME>
          <LENGTH>22</LENGTH>
        </SYSTEM-SIGNAL>
        <SYSTEM-SIGNAL>
          <SHORT-NAME>FaultClear_command</SHORT-NAME>
          <LENGTH>2</LENGTH>
        </SYSTEM-SIGNAL>
        

    </AR-PACKAGE>
    
    <AR-PACKAGE>
        <SHORT-NAME>A</SHORT-NAME>
        <CAN-CLUSTER>
          <SHORT-NAME>CAN</SHORT-NAME>
          <PHYSICAL-CHANNELS>
            <PHYSICAL-CHANNEL>
              <SHORT-NAME>CAN</SHORT-NAME>
              <FRAME-TRIGGERINGSS>
                <CAN-FRAME-TRIGGERING>
                  <SHORT-NAME>someFrame</SHORT-NAME>
                  <FRAME-PORT-REFS/>
                  <FRAME-REF>/B/CAN_FRAME_FD</FRAME-REF>
                  <I-PDU-TRIGGERING-REFS>
                    <I-PDU-TRIGGERING-REF DEST="I-PDU-TRIGGERING">/Cluster/CAN/IPDUTRIGG_CommandModeControl</I-PDU-TRIGGERING-REF>
                  </I-PDU-TRIGGERING-REFS>
                  <CAN-ADDRESSING-MODE>EXTENDED</CAN-ADDRESSING-MODE>
                  <IDENTIFIER>16755521</IDENTIFIER>
                </CAN-FRAME-TRIGGERING>
              </FRAME-TRIGGERINGSS>
            </PHYSICAL-CHANNEL>
          </PHYSICAL-CHANNELS>
        </CAN-CLUSTER>
            
        <I-SIGNAL>
          <SHORT-NAME>Enable_command</SHORT-NAME>
          <SYSTEM-SIGNAL-REF>/B/Enable_command</SYSTEM-SIGNAL-REF>
        </I-SIGNAL>
        <I-SIGNAL>
          <SHORT-NAME>FaultClear_command</SHORT-NAME>
          <SYSTEM-SIGNAL-REF>/B/FaultClear_command</SYSTEM-SIGNAL-REF>
        </I-SIGNAL>
        
        <I-SIGNAL-TO-I-PDU-MAPPING>
            <SHORT-NAME>SignalIPDUAssignment1</SHORT-NAME>
            <I-SIGNAL-REF>/A/Enable_command</I-SIGNAL-REF>
            <START-POSITION>63</START-POSITION>            
            <PACKING-BYTE-ORDER>MOST-SIGNIFICANT-BYTE-FIRST</PACKING-BYTE-ORDER>
        </I-SIGNAL-TO-I-PDU-MAPPING>
        <I-SIGNAL-TO-I-PDU-MAPPING>
            <SHORT-NAME>SignalIPDUAssignment2</SHORT-NAME>
            <I-SIGNAL-REF>/A/FaultClear_command</I-SIGNAL-REF>
            <START-POSITION>63</START-POSITION>            
            <PACKING-BYTE-ORDER>MOST-SIGNIFICANT-BYTE-FIRST</PACKING-BYTE-ORDER>
        </I-SIGNAL-TO-I-PDU-MAPPING>
        
        
        
        <CONTAINER-I-PDU>
            <SHORT-NAME>Frame_FD_CONTAINER</SHORT-NAME>
            <LENGTH>54</LENGTH>
            <CONTAINED-PDU-TRIGGERING-REFS>
                <CONTAINED-PDU-TRIGGERING-REF>/A/PT_PDU1</CONTAINED-PDU-TRIGGERING-REF>
                <CONTAINED-PDU-TRIGGERING-REF>/A/PT_PDU2</CONTAINED-PDU-TRIGGERING-REF>
            </CONTAINED-PDU-TRIGGERING-REFS>
        </CONTAINER-I-PDU>
        
        <PDU-TRIGGERING>
            <SHORT-NAME>PT_PDU1</SHORT-NAME>
            <I-PDU-REF>/B/PDU1</I-PDU-REF>
        </PDU-TRIGGERING>
        <PDU-TRIGGERING>
            <SHORT-NAME>PT_PDU2</SHORT-NAME>
            <I-PDU-REF>/B/PDU2</I-PDU-REF>
        </PDU-TRIGGERING>
                
    </AR-PACKAGE>
    </ARXML>
        
     ''').encode('utf-8'))
    matrix = canmatrix.formats.arxml.load(arxml, dbcImportEncoding="utf8")
    assert matrix["CAN"].frames[0].signals[0].name == 'Enable_command'
    assert matrix["CAN"].frames[0].signals[1].name == 'FaultClear_command'
