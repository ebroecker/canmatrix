#!/bin/sh
python setup.py install
cd test
./test.py
