import hashlib
import hmac
import json
from pathlib import Path
from cryptography.fernet import Fernet
from src.config import ROLES

class AcessoNegado(PermissionError):
    def __init__(self,message,perfil='nao_autenticado'):
        super().__init__(message);self.perfil=perfil
class IntegridadeError(ValueError):pass

def canon(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(data):return hashlib.sha256(data).hexdigest()
def key(base,name):return (Path(base)/'segredos'/name).read_bytes().strip()
def mac(base,data,name='assinatura.key'):return hmac.new(key(base,name),data,hashlib.sha256).hexdigest()
def pseudonimo(base,identifier):return mac(base,identifier.encode(),'pseudonimo.key')
def encrypt(base,data):return Fernet(key(base,'criptografia.key')).encrypt(data)
def decrypt(base,data):return Fernet(key(base,'criptografia.key')).decrypt(data)

def privado(path,data):
    with path.open('xb') as f:f.write(data)
    path.chmod(0o600)

def autenticar(conn,path,action):
    try:token=Path(path).read_bytes().strip()
    except OSError:raise AcessoNegado('Credencial nao encontrada ou inacessivel.') from None
    if len(token)>512:raise AcessoNegado('Credencial invalida.')
    hashed=digest(token)
    role=None
    for r in conn.execute('SELECT perfil,token_hash FROM credenciais'):
        if hmac.compare_digest(hashed,r['token_hash']):role=r['perfil']
    if role is None:raise AcessoNegado('Credencial invalida.')
    if action not in ROLES.get(role,set()):raise AcessoNegado('Perfil sem permissao para esta operacao.',role)
    return role
