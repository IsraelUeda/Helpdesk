import sys
from pathlib import Path

# Garante que o diretório 'backend' esteja no sys.path para importações consistentes
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
