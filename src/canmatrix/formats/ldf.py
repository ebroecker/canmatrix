from __future__ import absolute_import

import ldfparser
import canmatrix
import ldfparser.encoding


def load(f, **options):  # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    ldf = ldfparser.parseLDF(path=f.name)  # using f.name is not nice, but works

    db = canmatrix.CanMatrix()

    for lin_frame in ldf.frames:
        cm_frame = canmatrix.Frame()
        cm_frame.name = lin_frame.name
        cm_frame.arbitration_id = cm_frame.arbitration_id.from_compound_integer(lin_frame.frame_id)
        cm_frame.add_transmitter(lin_frame.publisher.name)
        cm_frame.size = lin_frame.length

        for mapping in lin_frame.signal_map:
            lin_signal = mapping[1]
            cm_signal = canmatrix.Signal()
            if lin_signal.name in ldf.converters:
                for converter in ldf.converters[lin_signal.name]._converters:
                    if isinstance(converter, ldfparser.encoding.LogicalValue):
                        cm_signal.add_values(converter.phy_value, converter.info)
                    if isinstance(converter, ldfparser.encoding.PhysicalValue):
                        cm_signal.offset = converter.offset
                        cm_signal.factor = converter.scale
                        cm_signal.unit = converter.unit
                        cm_signal.min = converter.phy_min
                        cm_signal.max = converter.phy_max

            cm_signal.name = lin_signal.name
            cm_signal.size = lin_signal.width
            cm_signal.initial_value = lin_signal.init_value
            for subscriber in lin_signal.subscribers:
                cm_signal.add_receiver(subscriber.name)
            cm_signal.start_bit = mapping[0]
            cm_frame.add_signal(cm_signal)
        db.add_frame(cm_frame)
    return db
