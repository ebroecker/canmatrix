

library/canmatrixGenerateJS.py
 flasche Bits bei nicht-vollständigen Bytes...


library/exportdbc.py
 add multiplex-support

library/exportdbf.py
 multiple Transmitter
	 db-parameter sind nicht ordendlich im Objekt abgelegt

library/exportkcd.py
 Kajak doesnt like my consumer-list -> research why?
 multiple Transmitter









library/importarxml.py
 default-frame-info for CAN-Simulation Motorola format is missing (only default signals available => calculation required
 Well, ..., this is the first attempt to import a arxml-file; I did this without reading any spec;  
 recievers of signals are missing
 MULTIPLEXED-I-PDU support!



library/importdbc.py
 support for: VERSION, NS, BS_, BA_DEF_DEF_, BA_DEF_, CM_ BO, CM_
			: multiple Frame Submitters (example Line: BO_TX_BU_ 0 : b,a; )



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
 multiple Transmitter



library/importxls.py
			 : correct DLC ermitteln
			, this is NOT in .xls?!



xlrd/__init__.py
from .book import Book, colname ###  #### formula also has `colname` (restricted to 256 cols)


