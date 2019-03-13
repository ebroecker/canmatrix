#!env python
from importlib import import_module
import sys
import logging
import canmatrix
import os
if sys.version_info > (3, 0):
    import io
else:
    import StringIO

logger = logging.getLogger(__name__)
moduleList = ["arxml", "cmcsv", "dbc", "dbf", "cmjson",
              "kcd", "fibex", "sym", "xls", "xlsx", "yaml"]
loadedFormats = []
supportedFormats = {}
extensionMapping = {}

for module in moduleList:
    try:
        import_module("canmatrix." + module)
        loadedFormats.append(module)
    except ImportError:
        logger.info("%s is not supported", module)

for loadedModule in loadedFormats:
    supportedFormats[loadedModule] = []
    moduleInstance = sys.modules["canmatrix." + loadedModule]
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


def loads(string, importType=None, key="", flatImport=None, encoding="utf-8",**options):
    if sys.version_info > (3, 0):
        if type(string) == str:
            string = bytes(string, encoding)
        fileObject = io.BytesIO(string)
    else:
        string = string.encode(encoding)
        fileObject = StringIO.StringIO(string)
    return load(fileObject, importType, key, flatImport, **options)


def loadp(path, importType=None, key="", flatImport=None, **options):
    with open(path, "rb") as fileObject:
        if not importType:
            for supportedImportType, extension in extensionMapping.items():
                if path.lower().endswith(extension) and "load" in supportedFormats[supportedImportType]:
                    importType = supportedImportType
                    break

        if importType:
            return load(fileObject, importType, key, flatImport, **options)
        else:
            logger.error("This file format is not supported for reading")
            return None
    return None

def load(fileObject, importType, key="", flatImport=None, **options):
    dbs = {}
    moduleInstance = sys.modules["canmatrix." + importType]
    if "clusterImporter" in supportedFormats[importType]:
        dbs = moduleInstance.load(fileObject, **options)
    else:
        dbs[key] = moduleInstance.load(fileObject, **options)

    if flatImport:
        for key in dbs:
            return dbs[key]
    else:
        return dbs


def dump(canMatrixOrCluster, fileObject, exportType, **options):
    moduleInstance = sys.modules["canmatrix." + exportType]
    if isinstance(canMatrixOrCluster, canmatrix.CanMatrix):
        moduleInstance.dump(canMatrixOrCluster, fileObject, **options)
    elif "clusterExporter" in supportedFormats[exportType]:
        moduleInstance.dump(canMatrixOrCluster, fileObject, **options)


def dumpp(canCluster, path, exportType=None, **options):
    if not exportType:
        for key, extension in extensionMapping.items():
            if path.lower().endswith("." + extension) and "dump" in supportedFormats[key]:
                exportType = key
                break
    if exportType:
        if "clusterExporter" in supportedFormats[exportType]:
            fileObject = open(path, "wb")
            dump(canCluster, fileObject, exportType, **options)
        else:
            for name in canCluster:
                if len(name) > 0:
                    (filepath, ext) = os.path.splitext(path)
                    outfile = filepath + "_" + name + ext
                else:
                    outfile = path
                db = canCluster[name]
                fileObject = open(outfile, "wb")
                dump(db, fileObject, exportType, **options)
                fileObject.close()
    else:
        logger.error("This file format is not supported for writing")

    return None
