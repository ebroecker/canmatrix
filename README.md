This peace of Software mainly helps to interprete several kinds of descriptionformats for can-communication.
Some of these formats can be written also.

As a sideeffect, this software helps to convert between can-matrix-description formats.

Therefor this software includes a "Python Can Matrix Object" which describes the Can-Communication (Boardunits, Frames, Signals, Values, ...)

There are some import- and some export-functions for this object.

Import-File-Formats:
.dbc
.dbf
.kcd
.arxml
.xls (xls-import is missing byteorder-information, because I could not find any byteorder in usual .xls-can-matrixes)

Export-File-Formats:
.dbc
.dbf
.kcd


Thus Currently partly working (x = validated):
* convert .dbc -> .kcd x
* convert .dbc -> .dbf x
* convert .dbc -> .dbc x
* convert .dbf -> .kcd
* convert .dbf -> .dbf
* convert .dbf -> .kcd
* convert .kcd -> .kcd
* convert .kcd -> .dbf
* convert .kcd -> .dbc
* convert .arxml -> .dbc x
* convert .arxml -> .dbf
* convert .arxml -> .kcd
* convert .xls(x) -> .kcd
* convert .xls(x) -> .dbf
* convert .xls(x) -> .dbc

* generate Busmaster Simulation out of .dbf/.dbc/.arxml


DISCLAIMER:
This is 'couchware', this software is coded on the couch while watching TV.
Thus, the quality is very bad!
DON'T USE IT FOR ANY SERIOUS WORK ON CARS!


Formatspecific:
* generate Busmaster Simulation out of .kcd will never work, because default-framedata missing


For a Windows you need python and lxml library for python. 
I use "active python" and installed lxml-package from active
lxml is nedded for .arxml and .kcd support
 
after download and with python in your path, you should be able to use:
./convert.py some-matrix.dbc some-matrix.dbf
./convert.py some-matrix.arxml some-matrix.dbc
...


Have Fun,
feel free to contact me for any suggestions
Eduard

