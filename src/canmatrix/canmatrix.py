import warnings
warnings.warn(
    "Importing from 'canmatrix.canmatrix' is deprecated. "
    "Use 'from canmatrix import ...' instead.",
    DeprecationWarning,
    stacklevel=2)
from canmatrix import CanMatrix, matrix_class