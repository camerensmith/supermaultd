# PyInstaller runtime hook: import numpy before pygame to avoid dispatcher tracer issues
import os
# Prefer bundled OpenBLAS/MKL and avoid stray site packages
os.environ.pop("PYTHONPATH", None)
try:
    import numpy  # noqa: F401
except Exception as _e:
    pass
