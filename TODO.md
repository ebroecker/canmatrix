





canmatrix/canmatrix.py
: Definitions should be imported with disassembling not as complete string



canmatrix/canmatrixGenerateJS.py
 wrong bits are used if signal is not















canmatrix/exportarxml.py
 Well, ..., this is the first attempt to export a arxml-file; I did this without reading any spec;
 recievers of signals are missing
: insert Speed - if possible
            : TRANSFER-PROPERTY: PENDING???
            : TRANSFER-PROPERTY: PENDING???









canmatrix/exportkcd.py
 : support for extended frames (https://github.com/julietkilo/CANBabel/blob/master/src/main/java/com/github/canbabel/canio/kcd/Message.java) :





















canmatrix/importarxml.py
 Well, ..., this is the first attempt to import a arxml-file; I did this without reading any spec;
    : use diagAddress for frame-classification
                    



canmatrix/importdbc.py
 support for: VERSION, NS, BS_, SIG_VALTYPE_, BA_DEF_REL == BA_DEF_??, BA_DEF_DEF_REL_ = BA_DEF_DEF_  ??



canmatrix/importdbf.py
 support for [START_PARAM_NODE_RX_SIG]
 support for [START_PARAM_NODE_TX_MSG]



canmatrix/importkcd.py
 baudrate missing
 name save
 defaults for CAN-Simulation missing
 LabelGroup not supported



canmatrix/importsym.py
 : the signalname should be unique. If same signal-name is used in different mux-ids, the signal-name should be unified. maybe this is an dbc-export-issue not an sym-import-issue
 : I don't know what to do with the "/p"-Options in the signal-definition
 : what is the differenze between SEND and SENDRECEIVE ?
: support for title example: Title="some title"
                             /p ???















test/test.py
 : support testing of xlsx
             : support testing of xlsx
                 : be more specific: OSError: [Errno 17] File exists: 'converted/from_arxml'
                 : https://github.com/ebroecker/canmatrix/issues/9



