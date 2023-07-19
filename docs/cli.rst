Command Line Interface
======================


1. **canconvert**:

    converts CAN database formats between all supported formats.
    
    Example: "*canconvert* someArSystemdescription.arxml file.dbc"

2. **cancompare**:

    compares 2 CAN databases (of different or same format).

    Example: "*cancompare* file1.dbc file2.dbc"


General
_______

If you properly install canmatrix using *pip,* the setuptools create
two ecxcutables for you: `canconvert` and `cancompare`. You can find these executables
near to your `python(.exe)`

If you aren't able to find the scripts, you can still run it as

::

$ python -m canmatrix.cli.compare [args]
$ python -m canmatrix.cli.convert [args]

To show help message/usage call ::

    $ canconvert -h
    $ canconvert --help


Another arguments are ::

    $ canconvert -v

Output verbosity


::

    $ canconvert -s

don't print status messages to stdout. (only errors)

::

    $ canconvert -f FORCE_OUTPUT

enforce output format, ignoring output file extension (e.g., -f csv)


Conversion of file formats
__________________________

**convert dbc file to xlsx:**

::

    $ canconvert source.dbc target.xlsx

**convert dbc file to dbf:**

::

    $ canconvert source.dbc target.dbf

**convert arxml file to dbc:**

::

    $ canconvert source.arxml target.dbc

Note: in case of ``.arxml`` there can be multiple can databases in.
Thus the target ``target.dbc`` may in this case be called ``BUS-NAME-IN-ARXML_target.dbc``.
There will be one target ``.dbc`` for each database in ``.arxml``.

Note: in case of ``.arxml`` CAN Frames can be in the Container PDU format.
In this case by default all PDU contained frame are converted to multiplexed frame.
This can be avoided with ``--ignorePduContainer/--no-ignorePduContainer`` option and
PDU contained frames will be dropped

You can even convert to the same format:

**convert dbc file to dbc:**

::

    $ canconvert source.dbc target.dbc

Multiple charset support:

**convert dbc file to dbc with different charset:**

::

    $ canconvert --dbcImportEncoding=iso-8859-1 --dbcImportCommentEncoding=cp-1252 --dbcExportEncoding=utf-8 --dbcExportCommentEncoding=utf-8 source.dbc target.dbc

This converts ``source.dbc`` where units are coded in ``iso-8859-1`` and comments are coded in ``cp-1252`` in a ``target.dbc`` where everything is coded in ``utf-8``.
Similar charset conversions are possible or even mandatory for following formats: dbc, dbf and sym.


possible Modifications:
_______________________

**delete zero sized signals:**

::

    $ canconvert --deleteZeroSignals source.dbc target.dbc

will delete signals with 0 bit length from matrix

**delete unwanted attributes from signals:**

::

    $ canconvert --deleteSignalAttributes GenMsgCycleTime,MyAttrib source.dbc target.dbc

will delete the attributes ``GenMsgCycleTime`` and ``MyAttrib`` from all signals in ``source.dbc`` and save the result in ``target.dbc``

**delete unwanted attributes from frames:**

::

    $ canconvert --deleteFrameAttributes GenMsgCycleTime,MyAttrib source.dbc target.dbc

will delete the attributes ``GenMsgCycleTime`` and ``MyAttrib`` from all frames in ``source.dbc`` and save the result in ``target.dbc``

**recalculate DLC:**

::

    $ canconvert --recalcDLC=max source.dbc target.dbc

this will recalculate DLC for each frame in ``source.dbc``.
In ``target.dlc``  the same DLC like in ``source.dbc`` will be stored, except the calculated DLC is bigger.
Than the calculated DLC will be stored.

**recalculate DLC:**

::

    $ canconvert --recalcDLC=force source.dbc target.dbc

this will recalculate DLC for each frame in ``source.dbc``.
In ``target.dlc`` the calculated DLC will be stored independently from ``source.dbc``.

**delete unneeded/obsolete defines:**

::

    $ canconvert --deleteObsoleteDefines source.dbc target.dbc

this will remove all defines which no attribute exist for in ``source.dbc`` and store the result in ``target.dlc``.

**delete ECU:**

::

    $ canconvert --deleteECU=myEcu,myEcu2 source.dbc target.dbc

this will remove ECUs ``myEcu`` and ``myEcu2`` in ``source.dbc`` and store the result in ``target.dlc``.

**rename ECU:**

::

    $ canconvert --renameECU=myEcu:myNewEcu,myEcu2:myNewEcu2 source.dbc target.dbc

this will load ``source.dbc`` and rename ECU ``myEcu`` in ``myNewEcu``  and ``myEcu2`` in ``myNewEcu2``.
The result is stored in ``target.dlc``.

**delete Frame:**

::

    $ canconvert --deleteFrame=myFrame,myFrame2 source.dbc target.dbc

this will remove frames ``myFrame`` and ``myFrame2`` in ``source.dbc`` and store the result in ``target.dlc``.

**rename Frame:**

::

    $ canconvert --renameFrame=myFrame:myNewFrame,myFrame2:myNewFrame2 source.dbc target.dbc

this will load ``source.dbc`` and rename frames ``myFrame`` in ``myNewFrame``  and ``myFrame2`` in ``myNewFrame2``.
The result is stored in ``target.dlc``.

**compress Frame:**

::

    $ canconvert --compressFrame=myFrame,myFrame2,someFrames* source.dbc target.dbc

this will load ``source.dbc`` and compress frames ``myFrame`` in ``myFrame2``  and all frames starting with ``someFrames``.
compress means, it tries to fill gaps between signals.
Works only for frames which have only big_endian signals or frames which have only little_endian singals
Frame name could be * which will compress all frames
The result is stored in ``target.dlc``.


**delete Signal:**

::

    $ canconvert --deleteSignal=mySignal,mySignal2 source.dbc target.dbc

this will remove signales ``mySignal`` and ``mySignal2`` in ``source.dbc`` and store the result in ``target.dlc``.

**rename Signal:**

::

    $ canconvert --renameSignal=mySignal:myNewSignal,mySignal2:myNewSignal2 source.dbc target.dbc

this will load ``source.dbc`` and rename signals ``mySignal`` in ``myNewSignal``  and ``mySignal2`` in ``myNewSignal2``.
The result is stored in ``target.dlc``.

::

  $ canconvert --signalNameFromAttrib=CompuMethodName source.ARXML target.dbc

this will load ``source.arxml`` and create ``target.dlc`` while all signals are named from CompuMethodName in ARXML.
Also known values from ARXML are SysSignalName and ISignalName

**canFD:**

::

    $ canconvert --setFrameFd=myFrame,myFrame2 source.dbc target.dbc

this will set frame-type of  ``myFrame`` and ``myFrame2`` in ``source.dbc`` to CANFD and store the result in ``target.dlc``
                        list) Syntax: --setFrameFd=myFrame1,mySecondFrame

::

    $ canconvert --unsetFrameFd=myFrame,myFrame2 source.dbc target.dbc

this will set frame-type of  ``myFrame`` and ``myFrame2`` in ``source.dbc`` to normal (not FD) and store the result in ``target.dlc``
                        list) Syntax: --unsetFrameFd=myFrame1,mySecondFrame


Extract and Merge:
__________________

**extract one ecu out of matrix**

::

    $ canconvert --ecus=REAR_ECU source.dbc target.dbc

This generates a ``target.dbc`` with all Informations out of ``source.dbc`` which are needed for ``REAR_ECU``.
All frames which are received or sent by ``REAR_ECU`` are extracted. Also all attributes of the frames and the ECU.
This is some *lite* ECU-Extract.

**extract multiple ecus out of matrix:**

::

    $ canconvert --ecus=FRONT_ECU,REAR_ECU source.dbc target.dbc

**extract matrix with frames which FRONT_ECU receives and with frames REAR_ECUS transmits:**

::

    $ canconvert --ecus=FRONT_ECU:rx,REAR_ECU:tx source.dbc target.dbc




**extract frame[s] out of matrix:**

::

    $ canconvert --frames=REAR_FRAME,FRONT_FRAME source.dbc target.dbc

Extracts the frames ``REAR_FRAME`` and ``FRONT_FRAME`` with the needed ECUs and attributes.

**merge multiple databases:**

::

    $ canconvert --merge=second.dbc source.dbc target.dbc

Merges ``source.dbc`` and ``second.dbc`` in ``target.dbc``.

**merge ECU from other  database:**

::

    $ canconvert --merge=second.dbc:ecu=REAR_ECU source.dbc target.dbc

Merges REAR_ECU out of ``second.dbc`` with ``source.dbc`` and store result in ``target.dbc``.

**merge FRAME from other database:**

::

    $ canconvert --merge=second.dbc:frame=REAR_FRAME source.dbc target.dbc

Merges REAR_FRAME out of ``second.dbc`` with ``source.dbc`` and store result in ``target.dbc``.

**combinations and multiple extraction possible:**

::

    $ canconvert --merge=second.dbc:ecu=REAR_ECU:ecu=FRONT_ECU:frame=FRAME1:FRAME=FRAME2 source.dbc target.dbc

Merges REAR_ECU and FRONT_ECU and FRAME1 and FRAME2 out of ``second.dbc`` with ``source.dbc`` and store result in ``target.dbc``.


Commandline overview
____________________

* all formats support im-/export of signals and frames

  -h, --help

			show help message and exit

  -v

  			Output verbosity

  -s

  			don't print status messages to stdout. (only errors)

  -f FORCE_OUTPUT

  			enforce output format, ignoring output file extension (e.g., -f csv)

  --deleteZeroSignals

  			delete zero length signals (signals with 0 bit length) from matrix default False

  --recalcDLC=RECALCDLC

                        recalculate dlc; max: use maximum of stored and calculated dlc; force: force new calculated dlc

  --jsonExportCanard

  			Export Canard compatible json format

  --ecus=ECUS

  			Copy only given ECUs (comma separated list) to target matrix

  --frames=FRAMES

  			Copy only given Framess (comma separated list) to target matrix

  --merge=MERGE

  			merge additional can databases. Syntax: --merge filename[:ecu=SOMEECU][:frame=FRAME1][:frame=FRAME2],filename2

  --deleteEcu=DELETEECU

                        delete Ecu form databases. (comma separated list) Syntax: --deleteEcu=myEcu,mySecondEcu

  --renameEcu=RENAMEECU

                        rename Ecu form databases. (comma separated list) Syntax: --renameEcu=myOldEcu:myNewEcu,mySecondEcu:mySecondNewEcu

  --deleteFrame=DELETEFRAME

                        delete Frame form databases. (comma separated list) Syntax: --deleteFrame=myFrame1,mySecondFrame

  --renameFrame=RENAMEFRAME

                        rename Frame form databases. (comma separated list) Syntax: --renameFrame=myOldFrame:myNewFrame,mySecondFrame:mySecondNewFrame

  --compressFrame=FRAME

                        compress Frame form databases.  Syntax: --compressFrame=frame1,frame2,*

  --deleteSignal=DELETESIGNAL

                        delete Signal form databases. (comma separated list) Syntax: --deleteSignal=mySignal1,mySecondSignal

  --renameSignal=RENAMESIGNAL

                        rename Signal form databases. (comma separated list) Syntax: --renameSignal=myOldSignal:myNewSignal,mySecondSignal:mySecondNewSignal

  --signalNameFromAttrib=ATTRIBUTENAME

                        change signal_name to given signal attribute Syntax: --signalNameFromAttrib=SysSignalName
                        Example --signalNameFromAttrib SysSignalName
                        ARXML known Attributes: SysSignalName, ISignalName, CompuMethodName


* dbc:

  --dbcImportEncoding

                        Import charset of dbc (relevant for units), maybe utf-8 default iso-8859-1

  --dbcImportCommentEncoding

                        Import charset of Comments in dbc default iso-8859-1

  --dbcExportEncoding

                        Export charset of dbc (relevant for units), maybe utf-8 default iso-8859-1

  --dbcExportCommentEncoding

                        Export charset of comments in dbc default iso-8859-1


* dbf:

  --dbfImportEncoding

                        Import charset of dbf, maybe utf-8 default iso-8859-1

  --dbfExportEncoding

                        Export charset of dbf, maybe utf-8 default iso-8859-1
* sym:

  --symImportEncoding

                        Import charset of sym format, maybe utf-8 default iso-8859-1

  --symExportEncoding

                        Export charset of sym format, maybe utf-8 default iso-8859-1

* xls(x):

  --xlsMotorolaBitFormat

                        Excel format for startbit of motorola coded signals. Valid values: msb, lsb, msbreverse default msbreverse. [more about starbits...](https://github.com/ebroecker/canmatrix/wiki/signal-Byteorder)

* csv/xls/xlsx:

  --additionalSignalAttributes//--additionalFrameAttributes
                        append additional signal/frame-colums to csv, example:
                        is_signed,attributes["GenSigStartValue"]



* arxml:

  --arxmlIgnoreClusterInfo
                        Ignore any can cluster info from arxml; Import all frames in one matrix default 0
  --arxmlExportVersion
                        Ignore any can cluster info from arxml; set arxml version to either 3.2.3 or 4.1.0, default is 3.2.3 


* yaml
* scapy
* lua
* json:

 --jsonExportCanard

                        Export Canard compatible json format

 --jsonMotorolaBitFormat
