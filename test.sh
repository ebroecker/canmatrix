#!/bin/sh
pip install -e .[arxml,kcd,fibex,xls,xlsx,yaml]
cd test
python ./test.py
