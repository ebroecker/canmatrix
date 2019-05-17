# -*- coding: utf-8 -*-
import canmatrix.formats.arxml
import pathlib2


def test_ecu_extract():
    here = pathlib2.Path(__file__).parent
    
    db = canmatrix.formats.arxml.load(str(here / "MyECU.ecuc.arxml"))['']
    assert db.frames is not None
    assert len(db.frames) == 2
    assert len(db.frames[0].signals) == 3
    assert len(db.frames[1].signals) == 1
