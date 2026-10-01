import sys
from pathlib import Path

# Add backend directory and backend/src to python sys.path
backend_dir = Path(__file__).resolve().parent
src_dir = backend_dir / "src"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
