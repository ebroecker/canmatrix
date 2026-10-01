import canmatrix.formats.dbc
import io

from canmatrix.CanMatrix import CanMatrix

def test_empty_matrix_export():
    db = CanMatrix()
    outdbf = io.BytesIO()
    canmatrix.formats.dump(db, outdbf, "dbf")

