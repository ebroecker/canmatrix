#!/bin/sh
pip install .[arxml,kcd,fibex,xls,xlsx,yaml]
cd test
python ./test.py
