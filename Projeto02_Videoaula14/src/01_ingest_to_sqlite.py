"""Atalho para a etapa ingerir; implementacao centralizada em src/pipeline.py."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from projeto import main
if __name__ == '__main__':
    raise SystemExit(main(['ingerir', *sys.argv[1:]]))
