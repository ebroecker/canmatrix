#!/usr/bin/env python

import sys
sys.path.append('..')
import canmatrix.importany as im

def createDecodeMacro(signal, prefix="", macrosource="source", source="source"):
    startBit = signal._startbit
    byteOrder = signal._byteorder
    length = signal._signalsize
    
    mask = ((0xffffffffffffffff)>> (64-length))

    startByte = int(startBit/8)
    startBitInByte = startBit % 8

    code = "#define getSignal%s%s(%s)  ((((%s[%d])>>%d" % (prefix, signal._name, macrosource, source, startByte, startBitInByte)
    currentTargetLength = (8-startBitInByte)

    if byteOrder == 1:
        endByte = int((startBit+length) / 8)
        if (startBit+length) %  8 == 0:
            endByte -= 1
        for count in range(startByte +1, endByte+1):
            code += "|(%s[%d])<<%d" % (source, count, currentTargetLength)
            currentTargetLength += 8
    
    else: # motorola / big-endian
        endByte = int((startByte * 8 + 8 - startBitInByte - length) / 8);

        for count in range(startByte-1, endByte-1, -1):
            code += "|%s[%d]<<%d" % (source, count, currentTargetLength)
            currentTargetLength += 8;

    code += ")&0x%X)" % (mask)

    if signal._valuetype != '+':
        msb_sign_mask = 1 << (length - 1);
        code += "^0x%x)-0x%x " % (msb_sign_mask,msb_sign_mask);
    else:
        code += ")"
    code += "\n"
    return code

def createDecodeMacrosForFrame(Frame, prefix="", macrosource="source", source="source"):
    code = ""    
    for signal in Frame._signals:
        code += createDecodeMacro(signal, prefix, macrosource, source)
    return code

def main():
    from optparse import OptionParser

    usage = """
    %prog [options] canDatabaseFile targetFile.c

    import-file: *.dbc|*.dbf|*.kcd|*.arxml|*.xls(x)|*.sym

    """

    parser = OptionParser(usage=usage)
    parser.add_option("", "--frame",
                                      dest="exportframe", default=None,
                                      help="create macros for Frame(s); Comma seperated list of Names ")
    parser.add_option("", "--ecu",
                                      dest="exportecu", default=None,
                                      help="create macros for Ecu(s) Comma seperated ")
 
    (cmdlineOptions, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    infile = args[0]
    outfile = args[1]
 
    dbs = im.importany(infile)
    db = next(iter(dbs.values()))

    sourceCode = ""
    if cmdlineOptions.exportframe == None and cmdlineOptions.exportecu == None:
        for frame in db._fl._list:
            sourceCode += createDecodeMacrosForFrame(frame, "_" + frame._name + "_")

    if cmdlineOptions.exportframe != None:
        for frameId in cmdlineOptions.exportframe.split(','):
            try: 
                frame = db.frameById(int(frameId))
            except ValueError:
                frame = db.frameByName(frameId)
            if frame != None:            
                sourceCode += createDecodeMacrosForFrame(frame, "_" + frame._name + "_")
         
    if cmdlineOptions.exportecu != None:
        ecuList = cmdlineOptions.exportecu.split(',')
        for frame in db._fl._list:
            for ecu in ecuList:
                if ecu in frame._Transmitter:
                    sourceCode += createDecodeMacrosForFrame(frame, "_" + frame._name + "_")
                for signal in frame._signals:
                    if ecu in signal._receiver:
                        sourceCode += createDecodeMacro(signal, "_" + frame._name + "_")
 
    cfile = open(outfile, "w")    
    cfile.write(sourceCode)
    cfile.close()    
    

if __name__ == '__main__':
    sys.exit(main())
 	

