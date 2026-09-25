"""Comandos executados no Bash/PowerShell/CMD, nao dentro de >>>."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def main(argv=None):
    p=argparse.ArgumentParser(description='Projeto 02 - Videoaula 14: ingestao e pre-processamento para ML')
    p.add_argument('comando',choices=['diagnostico','gerar','ingerir','preprocessar','treinar','avaliar','prever','tudo','testar'])
    p.add_argument('--pasta',type=Path,default=ROOT,help='Pasta dos dados, modelos e resultados; padrao: pasta do projeto.')
    p.add_argument('--semente',type=int,default=42,help='Usada somente por gerar e tudo.')
    p.add_argument('--linhas',type=int,default=1200,help='Base simulada; multiplo de 5, minimo 300. Somente gerar e tudo.')
    args=p.parse_args(argv)
    if args.comando=='diagnostico':
        import importlib.metadata as md
        print('Python:',sys.version.split()[0]);print('Executavel:',sys.executable)
        for name in ['numpy','pandas','scikit-learn','joblib','matplotlib']:
            try: print(name,md.version(name))
            except md.PackageNotFoundError: print(name,'AUSENTE: instale requirements.txt')
        return 0
    if args.comando=='testar':
        return subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT).returncode
    try:
        from src.pipeline import gerar,ingerir,preprocessar,treinar,avaliar,prever
        funcs={'gerar':gerar,'ingerir':ingerir,'preprocessar':preprocessar,'treinar':treinar,'avaliar':avaliar,'prever':prever}
        seq=list(funcs) if args.comando=='tudo' else [args.comando]
        for etapa in seq:
            if etapa=='gerar': gerar(args.pasta.resolve(),args.semente,args.linhas)
            else: funcs[etapa](args.pasta.resolve())
        print('Concluido. Pasta de trabalho:',args.pasta.resolve())
        return 0
    except ModuleNotFoundError as e:
        print(f'ERRO: dependencia ausente ({e.name}). Instale requirements.txt com o mesmo Python.',file=sys.stderr)
    except (ValueError,FileNotFoundError) as e:
        print('ERRO:',e,file=sys.stderr)
    except Exception as e:
        print(f'ERRO ({type(e).__name__}): {e}',file=sys.stderr)
    return 1

if __name__=='__main__': raise SystemExit(main())
