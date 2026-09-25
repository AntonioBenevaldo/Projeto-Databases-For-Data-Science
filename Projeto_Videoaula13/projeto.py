"""Interface unica: execute no terminal Bash/PowerShell/CMD, nao no prompt >>>."""
from pathlib import Path
import argparse
import os
import secrets
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def chamar_r(args):
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    exe = args.rscript or os.getenv('RSCRIPT_PATH') or shutil.which('Rscript')
    if not exe:
        raise ValueError('R nao localizado. Instale R e use --rscript "C:\\Program Files\\R\\R-x.y.z\\bin\\Rscript.exe" com o caminho real.')
    if args.comando == 'r-instalar':
        cmd = [exe,str(ROOT/'r/instalar.R'),args.banco]
    else:
        cmd = [exe,str(ROOT/'r/analisar.R'),str(ROOT),args.banco,args.inicio,args.fim,str(args.lote),str(Path(args.saida_r).resolve())]
    subprocess.run(cmd, check=True, cwd=ROOT, env=os.environ.copy())

def main():
    parser = argparse.ArgumentParser(description='Videoaula 13: banco de dados, Python e R.')
    parser.add_argument('comando',choices=['diagnostico','preparar','extrair','analisar','tudo','testar','r-instalar','r','comparar','configurar-postgres','postgres-iniciar','postgres-parar'])
    parser.add_argument('--banco',choices=['sqlite','postgres'],default='sqlite')
    parser.add_argument('--inicio',default='2026-01-01')
    parser.add_argument('--fim',default='2026-03-31')
    parser.add_argument('--lote',type=int,default=4)
    parser.add_argument('--saida',default=str(ROOT/'outputs/python'))
    parser.add_argument('--saida-r',default=str(ROOT/'outputs/r'))
    parser.add_argument('--rscript',help='Caminho completo de Rscript.exe quando nao esta no PATH.')
    args = parser.parse_args()
    try:
        if args.comando == 'diagnostico':
            import importlib.metadata as md
            print('Python:',sys.version.split()[0]); print('Executavel:',sys.executable)
            for pkg in ['pandas','SQLAlchemy','python-dotenv']:
                try: print(pkg,md.version(pkg))
                except md.PackageNotFoundError: print(pkg,'AUSENTE: instale requirements.txt')
            print('Rscript no PATH:',shutil.which('Rscript') or 'nao localizado')
            print('Docker no PATH:',shutil.which('docker') or 'nao localizado')
            return 0
        if args.comando == 'testar':
            return subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT).returncode
        if args.comando == 'configurar-postgres':
            path=ROOT/'.env'
            if path.exists(): print('.env ja existe; preservado.'); return 0
            with path.open('x',encoding='utf-8') as f:
                f.write('PGHOST=127.0.0.1\nPGPORT=5432\nPGDATABASE=videoaula13\nPGUSER=ds_user\nPGPASSWORD='+secrets.token_urlsafe(24)+'\n')
            print('.env criado com senha aleatoria. Nao publique esse arquivo.')
            return 0
        if args.comando.startswith('postgres-'):
            if not shutil.which('docker'): raise ValueError('Instale e abra Docker Desktop primeiro.')
            if not (ROOT/'.env').exists(): raise ValueError('Execute configurar-postgres primeiro.')
            action=['up','-d','--wait'] if args.comando.endswith('iniciar') else ['stop']
            return subprocess.run(['docker','compose','--project-directory',str(ROOT),*action],cwd=ROOT).returncode
        from app.pipeline import engine, inicializar, extrair, analisar, comparar, validar_periodo
        validar_periodo(args.inicio,args.fim,args.lote)
        if args.comando in ['r-instalar','r']: chamar_r(args); return 0
        if args.comando == 'comparar': comparar(args.saida,args.saida_r); return 0
        if args.comando == 'analisar': analisar(args.saida); return 0
        eng=engine(args.banco)
        try:
            if args.comando in ['preparar','tudo']: inicializar(eng)
            if args.comando in ['extrair','tudo']: extrair(eng,args.saida,args.inicio,args.fim,args.lote)
            if args.comando == 'tudo': analisar(args.saida)
        finally: eng.dispose()
        return 0
    except ModuleNotFoundError as exc:
        print(f'Dependencia ausente: {exc.name}. Execute python -m pip install -r requirements.txt',file=sys.stderr)
    except (ValueError,FileNotFoundError,AssertionError) as exc:
        print('ERRO:',str(exc),file=sys.stderr)
    except subprocess.CalledProcessError:
        print('ERRO: a etapa R falhou; confira a mensagem acima.',file=sys.stderr)
    except Exception as exc:
        # Mensagens de drivers podem conter enderecos e credenciais; nao as imprimir.
        print(f'ERRO ({type(exc).__name__}): confira dependencias, banco iniciado, .env e etapa preparar.',file=sys.stderr)
    return 1

if __name__ == '__main__':
    raise SystemExit(main())
