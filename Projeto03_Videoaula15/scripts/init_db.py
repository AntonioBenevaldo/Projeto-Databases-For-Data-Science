"""Atalho: preparar."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from projeto import main
if __name__=='__main__':raise SystemExit(main(['preparar',*sys.argv[1:]]))
