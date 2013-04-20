











library/exportdbc.py
 add multiplex-support



library/exportdbf.py
	 db-parameter sind nicht ordendlich im Objekt abgelegt



library/exportkcd.py
 Kajak doesnt like my consumer-list -> research why?









library/importarxml.py
 default-frame-info for CAN-Simulation is missing (only default signals available => calculation required
 Well, ..., this is the first attempt to import a arxml-file; I did this without reading any spec;  
 sender of frames and recievers of signals are missing
	newBo = Botschaft(int(idele.text), name.text, int(dlc.text), "")  Transmitter fehlt noch



library/importdbc.py
 support for: VERSION, NS, BS_, BA_DEF_DEF_, BA_DEF_, CM_



library/importdbf.py
 support for [START_PARAM_NET]
 support for [START_PARAM_NODE]
 support for [START_PARAM_MSG]
 support for [START_PARAM_SIG]
 support for [START_PARAM_NODE_RX_SIG]
 support for [START_PARAM_NODE_TX_MSG]
 support for [START_PARAM_VAL]
 support for [START_PARAM_NET_VAL]
 support for [START_PARAM_NODE_VAL]



library/importkcd.py
 baudrate missing
 name save
 defaults for CAN-Simulation missing
 LabelGroup not supported



