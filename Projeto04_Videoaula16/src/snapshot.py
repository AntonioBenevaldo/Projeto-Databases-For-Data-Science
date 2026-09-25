import json
from pathlib import Path
import re
import shutil
import tempfile
import hmac
import platform
import importlib.metadata
from src.config import ROOT,RAW,COLS,FILES,QUERY
from src.security import canon,digest,mac,encrypt,decrypt,IntegridadeError
from src.data import extrair,validar,transformar,csv_bytes,ler_csv,indicadores
from src.audit import utc

def selecionar(conn,version=None):
    if version is None:version=conn.execute('SELECT ativa FROM estado WHERE id=1').fetchone()[0]
    if not isinstance(version,str) or not re.fullmatch(r'v[0-9]{4}',version):raise ValueError('Informe uma versao existente, por exemplo v0001.')
    row=conn.execute('SELECT * FROM versoes WHERE versao=?',(version,)).fetchone()
    if row is None:raise ValueError('Versao nao encontrada.')
    return row

def conferir(base,conn,version=None):
    record=selecionar(conn,version);version=record['versao'];folder=base/'versoes'/version
    if folder.is_symlink() or (base/'versoes').is_symlink():raise IntegridadeError('Links simbolicos nao aceitos nos snapshots.')
    buffers={}
    for name in FILES|{'manifesto.json'}:
        p=folder/name
        if p.is_symlink() or not p.is_file():raise IntegridadeError('Arquivo da versao ausente ou nao permitido.')
        buffers[name]=p.read_bytes()
    if digest(buffers['manifesto.json'])!=record['manifesto_hash']:raise IntegridadeError('Manifesto difere do catalogo de versoes.')
    envelope=json.loads(buffers['manifesto.json']);body=envelope['conteudo']
    if not hmac.compare_digest(mac(base,canon(body)),envelope['hmac_sha256']):raise IntegridadeError('Autenticacao HMAC do manifesto falhou.')
    if body['versao']!=version or set(body['arquivos_sha256'])!=FILES:raise IntegridadeError('Contrato do manifesto invalido.')
    for n,d in body['arquivos_sha256'].items():
        if digest(buffers[n])!=d:raise IntegridadeError('Conteudo da versao foi alterado.')
    # Decriptacao em memoria: nao publica nem exporta o conteudo bruto.
    try:raw=decrypt(base,buffers['origem.csv.fernet'])
    except Exception:raise IntegridadeError('Copia cifrada invalida ou chave incorreta.') from None
    if digest(raw)!=body['origem_csv_sha256']:raise IntegridadeError('Origem cifrada nao corresponde ao manifesto.')
    return body,buffers

def publicar(base,conn,role,inicio,fim,created):
    rows=extrair(conn,inicio,fim);validar(rows);safe=transformar(base,rows)
    version=f"v{conn.execute('SELECT COUNT(*) FROM versoes').fetchone()[0]+1:04d}"
    if not re.fullmatch(r'v[0-9]{4}',version):raise ValueError('Limite de versoes do laboratorio atingido.')
    destination=base/'versoes'/version
    if destination.exists():raise ValueError('Pasta residual de versao existente. Use outra pasta de estudo ou investigue antes de continuar.')
    raw=csv_bytes(rows,RAW)
    files={'dados.csv':csv_bytes(safe,COLS),'origem.csv.fernet':encrypt(base,raw),'consulta.sql':QUERY.encode()}
    for n in ['esquema.json','catalogo.json','politicas.json']:files[n]=(ROOT/'governance'/n).read_bytes()
    schema=json.loads(files['esquema.json']);schema['colunas_origem']=RAW;schema['colunas_publicadas']=COLS
    files['esquema.json']=canon(schema)
    now=utc();ind=indicadores(safe)
    codefiles=[ROOT/'projeto.py',*(ROOT/'src').glob('*.py'),ROOT/'src/schema.sql',ROOT/'requirements.txt']
    body={'versao':version,'criada_utc':now,'perfil_criador':role,'inicio':inicio,'fim':fim,
          'linhas_origem':len(rows),'linhas_publicadas':len(safe),'indicadores':ind,
          'origem_csv_sha256':digest(raw),'arquivos_sha256':{n:digest(v) for n,v in files.items()},
          'codigo_sha256':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in codefiles},
          'versao_esquema':schema['versao'],'python':platform.python_version(),
          'cryptography':importlib.metadata.version('cryptography')}
    envelope=canon({'conteudo':body,'hmac_sha256':mac(base,canon(body))})
    temp=Path(tempfile.mkdtemp(prefix='preparando_',dir=base/'versoes'))
    # tempfile retorna caminho absoluto; Path evita depender do separador do Windows.
    try:
        for n,data in files.items():(temp/n).write_bytes(data)
        (temp/'manifesto.json').write_bytes(envelope)
        temp.rename(destination);created.append(destination)
        conn.execute('INSERT INTO versoes VALUES(?,?,?,?,?)',(version,now,digest(envelope),len(safe),ind['faturamento_centavos']))
        conn.execute('UPDATE estado SET ativa=? WHERE id=1',(version,))
    finally:
        if temp.exists():shutil.rmtree(temp)
    return {'versao':version,'ativa':version,**ind,'linhas_origem':len(rows)}

def comparar(base,conn,de,para):
    a,ab=conferir(base,conn,de);b,bb=conferir(base,conn,para)
    ar={r['pedido_id']:r for r in ler_csv(ab['dados.csv'])};br={r['pedido_id']:r for r in ler_csv(bb['dados.csv'])}
    added=sorted(br.keys()-ar.keys());removed=sorted(ar.keys()-br.keys())
    changed=sorted(k for k in ar.keys()&br.keys() if ar[k]!=br[k])
    variation=(len(br)-len(ar))/len(ar)*100 if ar else None
    threshold=json.loads(bb['politicas.json'])['alerta_variacao_volume_percentual']
    return {'de':a['versao'],'para':b['versao'],'adicionados':added,'removidos':removed,'alterados':changed,
            'delta_faturamento_centavos':b['indicadores']['faturamento_centavos']-a['indicadores']['faturamento_centavos'],
            'variacao_linhas_percentual':variation,'alerta_volume':variation is not None and abs(variation)>threshold,
            'nota':'Comparacao por pedido. Alerta de volume didatico, nao teste estatistico de drift.'}
