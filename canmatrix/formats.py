#!env python
from importlib import import_module
import sys
import logging
logger = logging.getLogger('root')
import canmatrix
import os

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
        logger.error("Error importing canmatrix." + module)

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


def loads(string, importType=None, key="", flatImport=None, **options):
    fileObject = StringIO.StringIO[string]
    return load(fileObject, importType, key, flatImport, **options)


def loadp(path, importType=None, key="", flatImport=None, **options):
    fileObject = open(path, "rb")
    if not importType:
        for key, extension in extensionMapping.items():
            if path.endswith(extension) and "load" in supportedFormats[key]:
                importType = key
                break

    if importType:
        return load(fileObject, importType, **options)
    else:
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
    if (sys.version_info > (3, 0) and type(canmatrix.canmatrix.CanMatrix()) == type(canMatrixOrCluster)) or \
       (sys.version_info < (3, 0) and type(canmatrix.CanMatrix()) == type(canMatrixOrCluster)):
        moduleInstance.dump(canMatrixOrCluster, fileObject, **options)
    elif "clusterExporter" in supportedFormats[exportType]:
        moduleInstance.dump(canMatrixOrCluster, fileObject, **options)


def dumpp(canCluster, path, exportType=None, **options):
    if not exportType:
        for key, extension in extensionMapping.items():
            if path.endswith("." + extension) and "dump" in supportedFormats[key]:
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

    return None
