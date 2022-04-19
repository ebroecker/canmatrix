Installation
============


Install *canmatrix* with either
::

    $ pip install canmatrix

or

::

    $ pip install .

This installs the *canmatrix* package into your python installation.
In addition to the *canmatrix* package there are 2 scripts installed with this package:


for additional formats [arxml, kcd, fibex, xls, xlsx] use syntax like:
::

    $ pip install git+https://github.com/ebroecker/canmatrix#egg=canmatrix[kcd]


If you are using a \*NIX-System, these scripts should be callable from command line

If you are using a Windows system, these scripts are usually installed at the location of your python installation.
For example `C:\\python3.4\\Scripts` or `C:\\python2.7\\Scripts`


Dependencies
____________

* Canmatrix depends on:

  * xlrd (http://www.python-excel.org/)
  * xlwt-future (https://pypi.python.org/pypi/xlwt-future)
  * XlsxWriter (https://github.com/jmcnamara/XlsxWriter)
  * PyYAML (https://pypi.python.org/pypi/pyaml)
  * lxml (https://pypi.python.org/pypi/lxml)