class canCluster(dict):

    def __init__(self, *arg, **kw):
        super(canCluster, self).__init__(*arg, **kw)
        self.update()

    def updateFrames(self):
        frameArray = []
        frameArrayName = []
        for matrixName in self:
            for frame in self[matrixName].frames:
                if frame._name not in frameArrayName:
                    frameArrayName.append(frame._name)
                    frameArray.append(frame)
                else:
                    index = frameArrayName.index(frame._name)
                    for transmitter in frame.transmitter:
                        frameArray[index].addTransmitter(transmitter)
                    for receiver in frame.receiver:
                        frameArray[index].addReceiver(receiver)
        self._frames = frameArray
        return frameArray

    def updateSignals(self):
        signalArray = []
        signalArrayName = []
        for matrixName in self:
            for frame in self[matrixName].frames:
                for signal in frame.signals:
                    if signal._name not in signalArrayName:
                        signalArrayName.append(signal._name)
                        signalArray.append(signal)
                    else:
                        index = signalArrayName.index(signal._name)
                        for receiver in signal.receiver:
                            signalArray[index].addReceiver(receiver)
        self._signals = signalArray

    def updateECUs(self):
        ECUArray = []
        ECUArrayName = []
        for matrixName in self:
            for ecu in self[matrixName].boardUnits:
                if ecu._name not in ECUArrayName:
                    ECUArrayName.append(ecu._name)
                    ECUArray.append(ecu)
        self._ecus = ECUArray

    def update(self):
        self.updateFrames()
        self.updateSignals()
        self.updateECUs()

    @property
    def ecus(self):
        if not self._ecus:
            self.updateECUs()
        return self._ecus

    @property
    def boardUnits(self):
        return self.ecus

    @property
    def frames(self):
        if not self._frames:
            self.updateFrames()
        return self._frames

    @property
    def signals(self):
        if not self._signals:
            self.updateSignals()
        return self._signals
