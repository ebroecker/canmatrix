#!/usr/bin/env python

import sys
sys.path.append('..')
import canmatrix.importany as im

def createDecodeMacro(signal, prefix=""):
    startBit = signal._startbit
    byteOrder = signal._byteorder
    length = signal._signalsize
    
    mask = ((0xffffffff)>> (32-length))

    startByte = int(startBit/8)
    startBitInByte = startBit % 8

    code = "#define getSignal%s%s(source)  ((source[%d]>>%d" % (prefix, signal._name, startByte, startBitInByte)
    currentTargetLength = (8-startBitInByte)

    if byteOrder == 0:
        endByte = int((startBit+length) / 8)
        if (startBit+length) %  8 == 0:
            endByte -= 1
        for count in range(startByte +1, endByte+1):
            code += "|source[%d]<<%d" % (count, currentTargetLength)
            currentTargetLength += 8
    
    else: # motorola / big-endian
        endByte = int((startByte * 8 + 8 - startBitInByte - length) / 8);

        for count in range(startByte-1, endByte-1, -1):
            code += "|source[%d]<<%d" % (count, currentTargetLength)
            currentTargetLength += 8;

    code += ")&=0x%X)\n" % (mask)
    return code

def createDecodeMacrosForFrame(Frame, prefix=""):
    code = ""    
    for signal in Frame._signals:
        code += createDecodeMacro(signal, prefix)
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
 
    db = im.importany(infile)

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
 	

