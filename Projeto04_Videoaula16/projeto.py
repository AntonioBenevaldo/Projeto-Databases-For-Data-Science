from pathlib import Path
import argparse
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parent

def main(argv=None):
    p=argparse.ArgumentParser(description='Projeto 04 - seguranca, governanca e versoes de dados')
    p.add_argument('comando',choices=['diagnostico','inicializar','publicar','simular-lote','listar','consultar','verificar','comparar','restaurar','auditoria','catalogo','tudo','testar'])
    p.add_argument('--pasta',type=Path,default=ROOT)
    p.add_argument('--credencial',type=Path,help='Caminho do arquivo .token; padrao: admin.token da pasta de estudo.')
    p.add_argument('--versao');p.add_argument('--de');p.add_argument('--para')
    p.add_argument('--inicio',default='2026-01-01');p.add_argument('--fim',default='2026-01-31')
    a=p.parse_args(argv)
    if a.comando=='testar':return subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT).returncode
    if a.comando=='diagnostico':
        import importlib.metadata as md
        print('Python:',sys.version.split()[0]);print('Executavel:',sys.executable)
        try:print('cryptography:',md.version('cryptography'))
        except md.PackageNotFoundError:print('Instale requirements.txt.')
        return 0
    try:
        from src.service import inicializar,chamar
        def show(result):print(json.dumps(result,ensure_ascii=False,indent=2))
        base=a.pasta.resolve()
        if a.comando=='inicializar':show(inicializar(base));return 0
        if a.comando=='tudo':
            show(inicializar(base))
            result=chamar(base,'publicar',a.credencial,inicio=a.inicio,fim=a.fim);show(result)
            show(chamar(base,'verificar',a.credencial,versao=result['versao']))
            show(chamar(base,'consultar',a.credencial,versao=result['versao']))
        else:show(chamar(base,a.comando,a.credencial,versao=a.versao,de=a.de,para=a.para,inicio=a.inicio,fim=a.fim))
        return 0
    except Exception as exc:
        # Nao imprimir consultas, linhas brutas, tokens ou chaves em erros inesperados.
        if isinstance(exc,(ValueError,PermissionError,FileNotFoundError)):print('ERRO:',str(exc),file=sys.stderr)
        else:print('ERRO:',type(exc).__name__,'- confira inicializacao, dependencias e arquivos.',file=sys.stderr)
        return 1
if __name__=='__main__':raise SystemExit(main())
