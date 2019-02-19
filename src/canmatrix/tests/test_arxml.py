# -*- coding: utf-8 -*-
import canmatrix.arxml
import pathlib

def test_ecu_extract():
    here = pathlib.Path(__file__).parent
    
    db = canmatrix.arxml.load(str(here / "MyECU.ecuc.arxml"))['']
    assert db.frames != None
    assert len(db.frames) == 2
    assert len(db.frames[0].signals) == 3
    assert len(db.frames[1].signals) == 1
        
