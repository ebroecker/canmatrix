def mergeFrame(frameId, sourceDb, targetDb):
    """
    This function copys a Frame identified by frameId from soruce-Canmatrix to target-Canmatrix
    while copying is easy, this function additionally copys all relevant Boardunits, and Defines
    """
    # check wether frameId is object, id or symbolic name
    if type(frameId).__name__ == 'int':
        frame = sourceDb.frameById(frameId)
    elif type(frameId).__name__ == 'Frame':
        frame = frameId
    else:
        frame = sourceDb.frameByName(frameId)

    if targetDb.frameById(frame._Id) != None:
        # frame already in targetdb...
        return

    # copy Frame-Object:
    targetDb._fl.addFrame(frame)

    ## Boardunits:
    # each transmitter of Frame could be ECU that is not listed already
    for transmitter in frame._Transmitter:
        targetBU = targetDb._BUs.byName(transmitter)
        sourceBU = sourceDb._BUs.byName(transmitter)
        if sourceBU is not None and targetBU is None:
            copyBU(sourceBU, sourceDb, targetDb)

    # trigger all signals of Frame
    for sig in frame._signals:
        # each receiver of Signal could be ECU that is not listed already
        for receiver in sig._receiver:
            targetBU = targetDb._BUs.byName(transmitter)
            sourceBU = sourceDb._BUs.byName(transmitter)
            if sourceBU is not None and targetBU is None:
                copyBU(sourceBU, sourceDb, targetDb)

    # copy all frame-defines
    attributes = frame._attributes
    for attribute in attributes:
        targetDb.addFrameDefines(attribute, sourceDb._frameDefines[attribute]._definition)
        targetDb.addDefineDefault(attribute, sourceDb._frameDefines[attribute]._defaultValue)

    # trigger all signals of Frame
    for sig in frame._signals:
        # delete all 'unknown' attributes
        attributes = sig._attributes
        for attribute in attributes:
            targetDb.addSignalDefines(attribute, sourceDb._signalDefines[attribute]._definition)
            targetDb.addDefineDefault(attribute, sourceDb._signalDefines[attribute]._defaultValue)
