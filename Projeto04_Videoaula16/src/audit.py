import json
import hmac
from datetime import datetime,timezone
from src.security import canon,mac,IntegridadeError

def utc():return datetime.now(timezone.utc).isoformat()
def verificar(base,conn):
    previous='0'*64;n=0
    for r in conn.execute('SELECT * FROM auditoria ORDER BY seq'):
        n+=1
        if r['seq']!=n or r['anterior']!=previous:raise IntegridadeError('Cadeia de auditoria inconsistente.')
        expected=mac(base,previous.encode()+r['payload'].encode())
        if not hmac.compare_digest(expected,r['assinatura']):raise IntegridadeError('Auditoria alterada.')
        if json.loads(r['payload'])['seq']!=n:raise IntegridadeError('Sequencia interna alterada.')
        previous=r['assinatura']
    return n,previous

def registrar(base,conn,role,action,status,details=None):
    n,previous=verificar(base,conn)
    body={'seq':n+1,'utc':utc(),'perfil':role,'acao':action,'status':status,'detalhes':details or {}}
    payload=canon(body).decode()
    conn.execute('INSERT INTO auditoria VALUES(?,?,?,?)',(n+1,payload,previous,mac(base,previous.encode()+payload.encode())))
