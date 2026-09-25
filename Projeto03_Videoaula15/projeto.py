from pathlib import Path
import argparse
import subprocess
import sys
ROOT=Path(__file__).resolve().parent

def main(argv=None):
    p=argparse.ArgumentParser(description='Projeto 03 - consultas automatizadas e pipeline incremental')
    p.add_argument('comando',choices=['diagnostico','preparar','executar','simular-lote','relatorio','historico','automatizar','tudo','testar'])
    p.add_argument('--pasta',type=Path,default=ROOT)
    p.add_argument('--limite',type=int,default=100,help='Maximo de eventos por execucao.')
    p.add_argument('--desde-evento',type=int,default=None,help='Reprocessar depois desta sequencia; nao pode pular o checkpoint.')
    p.add_argument('--tentativas',type=int,default=3)
    p.add_argument('--espera',type=float,default=1,help='Espera inicial dos retries; backoff limitado a 30s.')
    p.add_argument('--falha',choices=['nenhuma','transitoria','qualidade','carga'],default='nenhuma')
    p.add_argument('--intervalo',type=float,default=10,help='Espera apos o fim de cada ciclo da automacao.')
    p.add_argument('--repeticoes',type=int,default=3)
    args=p.parse_args(argv)
    if args.comando=='testar':return subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT).returncode
    if args.comando=='diagnostico':
        import importlib.metadata as md
        import sqlite3
        print('Python:',sys.version.split()[0]);print('Executavel:',sys.executable);print('SQLite:',sqlite3.sqlite_version)
        for pkg in ['pandas','SQLAlchemy']:
            try:print(pkg,md.version(pkg))
            except md.PackageNotFoundError:print(pkg,'AUSENTE: instale requirements.txt')
        return 0
    try:
        from src.config import pasta
        from src.demo import preparar,simular_lote
        from src.pipeline import executar,automatizar
        from src.observe import relatorio,historico
        base=pasta(args.pasta)
        opts={'limite':args.limite,'desde':args.desde_evento,'tentativas':args.tentativas,'espera':args.espera,'falha':args.falha}
        if args.comando=='preparar':preparar(base)
        elif args.comando=='simular-lote':simular_lote(base)
        elif args.comando=='relatorio':relatorio(base)
        elif args.comando=='historico':historico(base)
        elif args.comando=='automatizar':automatizar(base,args.intervalo,args.repeticoes,**opts)
        elif args.comando=='tudo':preparar(base);executar(base,**opts)
        else:executar(base,**opts)
        return 0
    except ModuleNotFoundError as exc:print(f'ERRO: instale requirements.txt; falta {exc.name}.',file=sys.stderr)
    except KeyboardInterrupt:return 130
    except Exception as exc:print(f'ERRO ({type(exc).__name__}): {exc}\nConfira a etapa preparar e os registros em outputs.',file=sys.stderr)
    return 1

if __name__=='__main__':raise SystemExit(main())
