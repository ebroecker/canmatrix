# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import importlib
import logging
import os
import sys
import typing
from builtins import str
from io import BytesIO

import canmatrix
import canmatrix.cancluster

logger = logging.getLogger(__name__)
moduleList = ["arxml", "csv", "dbc", "dbf", "json", "ldf",
              "kcd", "fibex", "sym", "xls", "xlsx", "yaml", "scapy", "wireshark", "odx"]

loadedFormats = []
supportedFormats = {}  # type: typing.MutableMapping[str, typing.MutableSequence[str]]
extensionMapping = {}

for module in moduleList:
    try:
        importlib.import_module("canmatrix.formats." + module)
        loadedFormats.append(module)
    except ImportError:
        logger.warning("%s is not supported", module)

for loadedModule in loadedFormats:
    supportedFormats[loadedModule] = []
    moduleInstance = sys.modules["canmatrix.formats." + loadedModule]
    if "load" in dir(moduleInstance):
        supportedFormats[loadedModule].append("load")
    if "dump" in dir(moduleInstance):
        supportedFormats[loadedModule].append("dump")
    if "clusterImporter" in dir(moduleInstance):
        supportedFormats[loadedModule].append("clusterImporter")
    if "clusterExporter" in dir(moduleInstance):
        supportedFormats[loadedModule].append("clusterExporter")
    if "extension" in dir(moduleInstance):
        supportedFormats[loadedModule].append("extension")
        extensionMapping[loadedModule] = moduleInstance.extension  # type: ignore
    else:
        extensionMapping[loadedModule] = loadedModule


def loads(string, import_type=None, key="", encoding="utf-8", **options):
    # type: (typing.Union[bytes,str], str, str, str, **str) -> typing.Union[typing.Dict[str, canmatrix.CanMatrix], None]
    bytes_str = string.encode(encoding=encoding) if isinstance(string, str) else string
    file_object = BytesIO(bytes_str)
    return load(file_object, import_type, key, **options)


def loads_flat(string, import_type=None, key="", **options):
    # type: (str, str, typing.Optional[str], **str) -> typing.Union[canmatrix.CanMatrix, None]
    dbs = loads(string, import_type, key, **options)
    return dbs.popitem()[1] if dbs else None


def loadp(path, import_type=None, key="", **options):
    # type: (str, str, str, **str) -> typing.Union[typing.Dict[str, canmatrix.CanMatrix], None]
    with open(path, "rb") as fileObject:
        if not import_type:
            for supportedImportType, extension in extensionMapping.items():
                if path.lower().endswith(extension) and "load" in supportedFormats[supportedImportType]:
                    import_type = supportedImportType
                    break

        if import_type:
            return load(fileObject, import_type, key, **options)
        else:
            logger.error("This file format is not supported for reading")
            return None


def loadp_flat(path, import_type=None, key="", **options):
    # type: (str, str, str, **str) -> typing.Union[canmatrix.CanMatrix, None]
    dbs = loadp(path, import_type, key, **options)
    return dbs.popitem()[1] if dbs else None


def load(file_object, import_type, key="", **options):
    # type: (typing.BinaryIO, str, str, **str) -> typing.Union[typing.Dict[str, canmatrix.CanMatrix], None]
    dbs = {}  # type: typing.Dict[str, canmatrix.CanMatrix]
    module_instance = sys.modules["canmatrix.formats." + import_type]
    if "clusterImporter" in supportedFormats[import_type]:
        dbs = module_instance.load(file_object, **options)  # type: ignore
    else:
        dbs[key] = module_instance.load(file_object, **options)  # type: ignore
    return dbs


def load_flat(file_object, import_type, key="", **options):
    # type: (typing.BinaryIO, str, str, **str) -> typing.Union[canmatrix.CanMatrix, None]
    dbs = load(file_object, import_type, key, **options)
    return dbs.popitem()[1] if dbs else None


def dump(can_matrix_or_cluster, file_object, export_type, **options):
    # type: (typing.Union[canmatrix.CanMatrix, typing.Mapping[str, canmatrix.CanMatrix]], typing.IO, str, **str) -> None
    module_instance = sys.modules["canmatrix.formats." + export_type]
    if isinstance(can_matrix_or_cluster, canmatrix.CanMatrix):
        module_instance.dump(can_matrix_or_cluster, file_object, **options)  # type: ignore
    elif "clusterExporter" in supportedFormats[export_type]:
        module_instance.dump(can_matrix_or_cluster, file_object, **options)  # type: ignore


def dumpp(can_cluster, path, export_type=None, **options):
    # type: (typing.Mapping[str, canmatrix.CanMatrix], str, str, **str) -> None
    if not export_type:
        for key, extension in extensionMapping.items():
            if path.lower().endswith("." + extension) and "dump" in supportedFormats[key]:
                export_type = key
                break
    if export_type:
        if "clusterExporter" in supportedFormats[export_type]:
            file_object = open(path, "wb")  # type: typing.IO
            dump(can_cluster, file_object, export_type, **options)
        else:
            for name in can_cluster:
                if len(name) > 0:
                    (file_path, ext) = os.path.splitext(path)
                    outfile = file_path + "_" + name + ext
                else:
                    outfile = path
                db = can_cluster[name]
                file_object = open(outfile, "wb")
                dump(db, file_object, export_type, **options)
                file_object.close()
    else:
        logger.error("This file format is not supported for writing")
