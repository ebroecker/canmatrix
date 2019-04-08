# Stubs for xlwt.Bitmap (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from .BIFFRecords import BiffRecord
from typing import Any

class ObjBmpRecord(BiffRecord):
    def __init__(self, row: Any, col: Any, sheet: Any, im_data_bmp: Any, x: Any, y: Any, scale_x: Any, scale_y: Any) -> None: ...

class ImRawDataBmpRecord(BiffRecord):
    def __init__(self, data: Any) -> None: ...

class ImDataBmpRecord(ImRawDataBmpRecord):
    def __init__(self, filename: Any) -> None: ...
