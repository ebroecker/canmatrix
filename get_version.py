import sys

import versioneer


sys.stdout.write(versioneer.get_versions()["version"])
