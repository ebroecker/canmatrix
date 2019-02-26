#!env python
from importlib import import_module
import sys
import logging
import os
import typing

import canmatrix
if sys.version_info > (3, 0):
    import io
else:
    import StringIO

logger = logging.getLogger(__name__)
moduleList = ["arxml", "cmcsv", "dbc", "dbf", "cmjson",
              "kcd", "fibex", "sym", "xls", "xlsx", "yaml"]
loadedFormats = []
supportedFormats = {}  # type: typing.MutableMapping[str, typing.MutableSequence[str]]
extensionMapping = {}

for module in moduleList:
    try:
        import_module("canmatrix.formats." + module)
        loadedFormats.append(module)
    except ImportError:
        logger.info("%s is not supported", module)

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
        extensionMapping[loadedModule] = moduleInstance.extension
    else:
        extensionMapping[loadedModule] = loadedModule


def loads(string, import_type=None, key="", flat_import=None, encoding="utf-8", **options):
    if sys.version_info > (3, 0):
        if type(string) == str:
            string = bytes(string, encoding)
        file_object = io.BytesIO(string)
    else:
        string = string.encode(encoding)
        file_object = StringIO.StringIO(string)
    return load(file_object, import_type, key, flat_import, **options)


def loadp(path, import_type=None, key="", flat_import=None, **options):
    with open(path, "rb") as fileObject:
        if not import_type:
            for supportedImportType, extension in extensionMapping.items():
                if path.lower().endswith(extension) and "load" in supportedFormats[supportedImportType]:
                    import_type = supportedImportType
                    break

        if import_type:
            return load(fileObject, import_type, key, flat_import, **options)
        else:
            logger.error("This file format is not supported for reading")
            return None


def load(file_object, import_type, key="", flat_import=None, **options):
    dbs = {}
    module_instance = sys.modules["canmatrix.formats." + import_type]
    if "clusterImporter" in supportedFormats[import_type]:
        dbs = module_instance.load(file_object, **options)
    else:
        dbs[key] = module_instance.load(file_object, **options)

    if flat_import:
        for key in dbs:
            return dbs[key]
    else:
        return dbs


def dump(can_matrix_or_cluster, file_object, export_type, **options):
    module_instance = sys.modules["canmatrix.formats." + export_type]
    if isinstance(can_matrix_or_cluster, canmatrix.CanMatrix):
        module_instance.dump(can_matrix_or_cluster, file_object, **options)
    elif "clusterExporter" in supportedFormats[export_type]:
        module_instance.dump(can_matrix_or_cluster, file_object, **options)


def dumpp(can_cluster, path, export_type=None, **options):
    if not export_type:
        for key, extension in extensionMapping.items():
            if path.lower().endswith("." + extension) and "dump" in supportedFormats[key]:
                export_type = key
                break
    if export_type:
        if "clusterExporter" in supportedFormats[export_type]:
            file_object = open(path, "wb")
            dump(can_cluster, file_object, export_type, **options)
        else:
            for name in can_cluster:
                if len(name) > 0:
                    (filepath, ext) = os.path.splitext(path)
                    outfile = filepath + "_" + name + ext
                else:
                    outfile = path
                db = can_cluster[name]
                file_object = open(outfile, "wb")
                dump(db, file_object, export_type, **options)
                file_object.close()
    else:
        logger.error("This file format is not supported for writing")

    return None
