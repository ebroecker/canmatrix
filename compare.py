#!/usr/bin/env python3

from __future__ import print_function
from builtins import *
import canmatrix.importany as im
from canmatrix.compare import *
import sys
import codecs

#Copyright (c) 2013, Eduard Broecker
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#DAMAGE.


def dumpResult(res, depth = 0):
    if res._type is not None and res._result != "equal":
        for i in range(0,depth):
            print(" ", end=' ')
        print(res._type + " " + res._result + " ", end=' ')
        if  hasattr(res._ref, '_name'):
            print(res._ref._name)
        else:
            print(" ")
        if  res._changes is not None and res._changes[0] is not None and res._changes[1] is not None:
            for i in range(0,depth):
                print(" ", end=' ')
            print("old: " + str(res._changes[0].encode('ascii','replace')) + " new: " + str(res._changes[1].encode('ascii','replace')))
    for child in res._children:
        dumpResult(child, depth+1)

def main():
    if len(sys.argv) < 3:
        sys.stderr.write('Usage: sys.argv[0] matrix1 matrix2\n')
        sys.stderr.write('matrixX can be any of *.dbc|*.dbf|*.kcd|*.arxml\n')
        sys.exit(1)

    matrix1 = sys.argv[1]
    matrix2 = sys.argv[2]

    print("Importing " + matrix1 + " ... ")
    db1 = im.importany(matrix1)
    print("%d Frames found" % (db1._fl._list.__len__()))

    print("Importing " + matrix2 + " ... ")
    db2 = im.importany(matrix2)
    print("%d Frames found" % (db2._fl._list.__len__()))


    print("\n\n")


    ignore = {}
    #ignore["ATTRIBUTE"] = "*"
    #ignore["DEFINE"] = "*"
    obj = compareDb(db1, db2, ignore)
    dumpResult(obj)

if __name__ == '__main__':
    sys.exit(main())
