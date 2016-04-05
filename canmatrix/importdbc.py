from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import logging
logger = logging.getLogger('root')

from builtins import *
import math
#!/usr/bin/env python
#Copyright (c) 2013, Eduard Broecker
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#DAMAGE.

#
# this script imports dbc-files to a canmatrix-object
# dbc-files are the can-matrix-definitions of canoe
#
#TODO support for: VERSION, NS, BS_, SIG_VALTYPE_, BA_DEF_REL == BA_DEF_??, BA_DEF_DEF_REL_ = BA_DEF_DEF_  ??

from .canmatrix import *
import re
import codecs


def importDbc(filename, **options):
    if 'dbcImportEncoding' in options:
        dbcImportEncoding=options["dbcImportEncoding"]
    else:
        dbcImportEncoding='iso-8859-1'
    if 'dbcImportCommentEncoding' in options:
        dbcCommentEncoding=options["dbcImportCommentEncoding"]
    else:
        dbcCommentEncoding=dbcImportEncoding

    i = 0
    class FollowUps(object):
        nothing, signalComment, frameComment, boardUnitComment, globalComment = list(range(5))
    followUp = FollowUps.nothing
    comment = ""
    signal = None
    frame = None
    boardUnit = None
    db = CanMatrix()
    f = open(filename, 'rb')
    for line in f:
        i = i+1
        l = line.strip()
        if l.__len__() == 0:
            continue
        if followUp == FollowUps.signalComment:
            try:
                comment += "\n" + l.decode(dbcCommentEncoding).replace('\\"','"')
            except:
                logger.error("Error decoding line: %d (%s)" % (i, line))
            if l.endswith(b'";'):
                followUp = FollowUps.nothing
                if signal is not None:
                    signal.addComment(comment[0:-2])
            continue;
        elif followUp == FollowUps.frameComment:
            try:
                comment += "\n" + l.decode(dbcCommentEncoding).replace('\\"','"')
            except:
                logger.error("Error decoding line: %d (%s)" % (i, line))
            if l.endswith(b'";'):
                followUp = FollowUps.nothing
                if frame is not None:
                    frame.addComment(comment[0:-2])
            continue;
        elif followUp == FollowUps.boardUnitComment:
            try:
                comment += "\n" + l.decode(dbcCommentEncoding).replace('\\"','"')
            except:
                logger.error("Error decoding line: %d (%s)" % (i, line))
            if l.endswith(b'";'):
                followUp = FollowUps.nothing
                if boardUnit is not None:
                    boardUnit.addComment(comment[0:-2])
            continue;
        decoded = l.decode(dbcImportEncoding)
        if decoded.startswith("BO_ "):
            regexp = re.compile("^BO\_ (\w+) (\w+) *: (\w+) (\w+)")
            temp = regexp.match(decoded)
#            db._fl.addFrame(Frame(temp.group(1), temp.group(2), temp.group(3), temp.group(4)))
            db._fl.addFrame(Frame(temp.group(2), 
                                  Id=temp.group(1),
                                  dlc=temp.group(3),
                                  transmitter=temp.group(4)))
        elif decoded.startswith("SG_ "):
            pattern = "^SG\_ (\w+) : (\d+)\|(\d+)@(\d+)([\+|\-]) \(([0-9.+\-eE]+),([0-9.+\-eE]+)\) \[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] \"(.*)\" (.*)"
            regexp = re.compile(pattern)
            temp = regexp.match(decoded)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp_raw = regexp_raw.match(l)
            if temp:
                receiver = list(map(str.strip, temp.group(11).split(',')))

                tempSig = Signal(temp.group(1), 
                                startBit=temp.group(2), 
                                signalSize=temp.group(3), 
                                is_little_endian=(int(temp.group(4))==1),
                                is_signed = (temp.group(5)=='-'), 
                                factor=temp.group(6), 
                                offset=temp.group(7),
                                min=temp.group(8),
                                max=temp.group(9),
                                unit=temp_raw.group(10).decode(dbcImportEncoding),
                                receiver=receiver)     
                if not tempSig._is_little_endian:
                    # startbit of motorola coded signals are MSB in dbc
                    tempSig.setMsbStartbit(int(temp.group(2)))                
                db._fl.addSignalToLastFrame(tempSig)
            else:
                pattern = "^SG\_ (\w+) (\w+) *: (\d+)\|(\d+)@(\d+)([\+|\-]) \(([0-9.+\-eE]+),([0-9.+\-eE]+)\) \[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] \"(.*)\" (.*)"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                receiver = list(map(str.strip, temp.group(12).split(',')))
                multiplex = temp.group(2)
                if multiplex == 'M':
                    multiplex = 'Multiplexor'
                else:
                    multiplex = int(multiplex[1:])
                tempSig = Signal(temp.group(1), 
                                  startBit = temp.group(3), 
                                  signalSize = temp.group(4),
                                  is_little_endian=(int(temp.group(5))==1), 
                                  is_signed = (temp.group(6)=='-'), 
                                  factor=temp.group(7), 
                                  offset=temp.group(8),
                                  min=temp.group(9),
                                  max=temp.group(10),
                                  unit=temp_raw.group(11).decode(dbcImportEncoding),
                                  receiver=receiver,
                                  multiplex=multiplex)     
                if not tempSig._is_little_endian:
                    # startbit of motorola coded signals are MSB in dbc
                    tempSig.setMsbStartbit(int(temp.group(3)))                
                
                db._fl.addSignalToLastFrame(tempSig)


        elif decoded.startswith("BO_TX_BU_ "):
            regexp = re.compile("^BO_TX_BU_ ([0-9]+) *: *(.+);")
            temp = regexp.match(decoded)
            botschaft = db.frameById(temp.group(1))
            for bu in temp.group(2).split(','):
                botschaft.addTransmitter(bu)
        elif decoded.startswith("CM_ SG_ "):
            pattern = "^CM\_ SG\_ *(\w+) *(\w+) *\"(.*)\";"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                botschaft = db.frameById(temp.group(1))
                signal = botschaft.signalByName(temp.group(2))
                if signal:
                    try:
                        signal.addComment(temp_raw.group(3).decode(dbcCommentEncoding).replace('\\"','"'))
                    except:
                        logger.error("Error decoding line: %d (%s)" % (i, line))
            else:
                pattern = "^CM\_ SG\_ *(\w+) *(\w+) *\"(.*)"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    botschaft = db.frameById(temp.group(1))
                    signal = botschaft.signalByName(temp.group(2))
                    try:
                        comment = temp_raw.group(3).decode(dbcCommentEncoding).replace('\\"','"')
                    except:
                        logger.error("Error decoding line: %d (%s)" % (i, line))
                    followUp = FollowUps.signalComment

        elif decoded.startswith("CM_ BO_ "):
            pattern = "^CM\_ BO\_ *(\w+) *\"(.*)\";"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                frame = db.frameById(temp.group(1))
                if frame:
                    try:
                        frame.addComment(temp_raw.group(2).decode(dbcCommentEncoding).replace('\\"','"'))
                    except:
                        logger.error("Error decoding line: %d (%s)" % (i, line))
            else:
                pattern = "^CM\_ BO\_ *(\w+) *\"(.*)"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    frame = db.frameById(temp.group(1))
                    try:
                        comment = temp_raw.group(2).decode(dbcCommentEncoding).replace('\\"','"')
                    except:
                        logger.error("Error decoding line: %d (%s)" % (i, line))
                    followUp = FollowUps.frameComment
        elif decoded.startswith("CM_ BU_ "):
            pattern = "^CM\_ BU\_ *(\w+) *\"(.*)\";"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                boardUnit = db.boardUnitByName(temp.group(1))
                if boardUnit:
                    try:
                        boardUnit.addComment(temp_raw.group(2).decode(dbcCommentEncoding).replace('\\"','"'))
                    except:
                        logger.error("Error decoding line: %d (%s)" % (i, line))
            else:
                pattern = "^CM\_ BU\_ *(\w+) *\"(.*)"
                regexp = re.compile(pattern)
                regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
                temp = regexp.match(decoded)
                temp_raw = regexp_raw.match(l)
                if temp:
                    boardUnit = db.boardUnitByName(temp.group(1))
                    if boardUnit:
                        try:
                            comment = temp_raw.group(2).decode(dbcCommentEncoding).replace('\\"','"')
                        except:
                            logger.error("Error decoding line: %d (%s)" % (i, line))
                        followUp = FollowUps.boardUnitComment
        elif decoded.startswith("BU_:"):
            pattern = "^BU\_\:(.*)"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            if temp:
                myTempListe = temp.group(1).split(' ')
                for ele in myTempListe:
                    if len(ele.strip()) > 1:
                        db._BUs.add(BoardUnit(ele))

        elif decoded.startswith("VAL_ "):
            regexp = re.compile("^VAL\_ (\w+) (\w+) (.*);")
            temp = regexp.match(decoded)
            if temp:
                botschaftId = temp.group(1)
                signal = temp.group(2)
                tempList = temp.group(3).split('"')
                try:
                    for i in range(math.floor(len(tempList)/2)):
                        bo = db.frameById(botschaftId)
                        sg = bo.signalByName(signal)
                        val = tempList[i*2+1]
                        #[1:-1]

                        if sg:
                            sg.addValues(tempList[i*2], val)
                except:
                    logger.error("Error with Line: " + str(tempList))

        elif decoded.startswith("VAL_TABLE_ "):
            regexp = re.compile("^VAL\_TABLE\_ (\w+) (.*);")
            temp = regexp.match(decoded)
            if temp:
                tableName = temp.group(1)
                tempList = temp.group(2).split('"')
                try:
                    valHash = {}
                    for i in range(math.floor(len(tempList)/2)):
                        val = tempList[i*2+1]
                        valHash[tempList[i*2].strip()] = val.strip()
                except:
                    logger.error("Error with Line: " + str(tempList))
                db.addValueTable(tableName, valHash)
            else:
                logger.debug(l)

        elif decoded.startswith("BA_DEF_ SG_ "):
            pattern = "^BA\_DEF\_ SG\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addSignalDefines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))
        elif decoded.startswith("BA_DEF_ BO_ "):
            pattern = "^BA\_DEF\_ BO\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addFrameDefines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))
        elif decoded.startswith("BA_DEF_ BU_ "):
            pattern = "^BA\_DEF\_ BU\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addBUDefines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))
        elif decoded.startswith("BA_DEF_ "):
            pattern = "^BA\_DEF\_ +\"([A-Za-z0-9\-_]+)\" +(.+);"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addGlobalDefines(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))

        elif decoded.startswith("BA_ "):
            regexp = re.compile("^BA\_ +\"[A-Za-z0-9\-_]+\" +(.+)")
            tempba = regexp.match(decoded)

            if tempba.group(1).strip().startswith("BO_ "):
                regexp = re.compile("^BA\_ \"(.*)\" BO\_ (\w+) (.+);")
                temp = regexp.match(decoded)
                db.frameById(int(temp.group(2))).addAttribute(temp.group(1),temp.group(3))
            elif tempba.group(1).strip().startswith("SG_ "):
                regexp = re.compile("^BA\_ \"(.*)\" SG\_ (\w+) (\w+) (.+);")
                temp = regexp.match(decoded)
                db.frameById(int(temp.group(2))).signalByName(temp.group(3)).addAttribute(temp.group(1),temp.group(4))
            elif tempba.group(1).strip().startswith("BU_ "):
                regexp = re.compile("^BA\_ \"(.*)\" BU\_ (\w+) (.+);")
                temp = regexp.match(decoded)
                db._BUs.byName(temp.group(2)).addAttribute(temp.group(1), temp.group(3))
            else:
                regexp = re.compile("^BA\_ \"([A-Za-z0-9\-\_]+)\" +([\"A-Za-z0-9\-\_]+);")
                temp = regexp.match(decoded)
                if temp:
                    db.addAttribute(temp.group(1),temp.group(2))


        elif decoded.startswith("SIG_GROUP_ "):
            regexp = re.compile("^SIG\_GROUP\_ +(\w+) +(\w+) +(\w+) +\:(.*);")
            temp = regexp.match(decoded)
            frame = db.frameById(temp.group(1))
            if frame is not None:
                signalArray = temp.group(4).split(' ')
                frame.addSignalGroup(temp.group(2), temp.group(3), signalArray)
        elif decoded.startswith("BA_DEF_DEF_ "):
            pattern = "^BA\_DEF\_DEF\_ +\"([A-Za-z0-9\-_]+)\" +(.+)\;"
            regexp = re.compile(pattern)
            regexp_raw = re.compile(pattern.encode(dbcImportEncoding))
            temp = regexp.match(decoded)
            temp_raw = regexp_raw.match(l)
            if temp:
                db.addDefineDefault(temp.group(1), temp_raw.group(2).decode(dbcImportEncoding))
#               else:
#                       print "Unrecocniced line: " + l + " (%d) " % i

    for bo in db._fl._list:
        # receiver is only given in the signals, so do propagate the receiver to the frame:
        bo.updateReceiver();        
        # extended-flag is implicite in canid, thus repair this:
        if bo._Id > 0x80000000:
            bo._Id -= 0x80000000
            bo._extended = 1
    return db
