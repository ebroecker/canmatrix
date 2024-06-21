import canmatrix.formats.dbc
import io


def test_empty_matrix_export():
    db = canmatrix.CanMatrix()
    outdbf = io.BytesIO()
    canmatrix.formats.dump(db, outdbf, "dbf")

