"""Preparação e execução em Python 3.14, pelo Bash, PowerShell ou CMD."""
from pathlib import Path
import json
import os
import struct
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv314'
PYTHON = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def main():
    if sys.version_info[:2] != (3, 14):
        print('Use Python 3.14: py -3.14 executar.py instalar', file=sys.stderr)
        return 1
    if struct.calcsize('P') * 8 != 64:
        print('Esta edição requer Python de 64 bits.', file=sys.stderr)
        return 1
    args = sys.argv[1:]
    if not args:
        print('Uso: py -3.14 executar.py instalar | diagnostico | tudo | testar')
        print('Outros comandos e opções de projeto.py também são aceitos.')
        return 0
    try:
        if args[0] == 'instalar':
            if len(args) != 1:
                raise ValueError('Use apenas: py -3.14 executar.py instalar')
            if not ENV.exists():
                print('Criando .venv314 com Python', sys.version.split()[0], flush=True)
                venv.EnvBuilder(with_pip=True).create(ENV)
            if not PYTHON.is_file():
                raise ValueError('A pasta .venv314 está incompleta. Renomeie-a e repita instalar.')
            info = json.loads(subprocess.check_output([
                str(PYTHON), '-c',
                'import sys,struct,json;print(json.dumps([list(sys.version_info[:2]),struct.calcsize("P")*8]))'
            ], text=True))
            if info != [[3, 14], 64]:
                raise ValueError('A .venv314 existente não usa Python 3.14 de 64 bits. Renomeie-a e repita instalar.')
            subprocess.run([str(PYTHON), '-m', 'pip', 'install', '--only-binary=:all:',
                            '-r', str(ROOT / 'requirements.txt')], cwd=ROOT, check=True)
            args = ['diagnostico']
        if not PYTHON.is_file():
            raise ValueError('Primeiro execute: py -3.14 executar.py instalar')
        return subprocess.run([str(PYTHON), str(ROOT / 'projeto.py'), *args], cwd=ROOT).returncode
    except (ValueError, OSError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print('A etapa falhou. Confira a mensagem acima antes de continuar.', file=sys.stderr)
        return exc.returncode or 1
    except KeyboardInterrupt:
        print('Execução interrompida.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
