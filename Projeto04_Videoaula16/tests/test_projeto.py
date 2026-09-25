from pathlib import Path
from contextlib import closing
from unittest.mock import patch
import json
import sqlite3
import tempfile
import unittest
from src.service import inicializar,chamar,conectar
from src.security import AcessoNegado,IntegridadeError,decrypt,digest,pseudonimo
from src.snapshot import conferir
from src.audit import verificar
from src.data import extrair,validar

class ProjetoTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='governanca 16 ')
        self.base=Path(self.tmp.name);inicializar(self.base)
    def tearDown(self):self.tmp.cleanup()
    def call(self,action,role='admin',**kw):return chamar(self.base,action,self.base/'segredos'/f'{role}.token',**kw)
    def publish(self):return self.call('publicar')
    def audit(self):
        with closing(conectar(self.base)) as conn:return [json.loads(r[0]) for r in conn.execute('SELECT payload FROM auditoria ORDER BY seq')]
    def test_01_inicializacao_preserva_chaves(self):
        before=(self.base/'segredos/criptografia.key').read_bytes()
        self.assertEqual(inicializar(self.base)['estado'],'ja_inicializado')
        self.assertEqual(before,(self.base/'segredos/criptografia.key').read_bytes())
    def test_02_publicacao_totais(self):
        r=self.publish()
        self.assertEqual((r['versao'],r['pedidos_concluidos'],r['faturamento_centavos'],r['custo_total_centavos'],r['lucro_bruto_centavos']),('v0001',4,57500,37000,20500))
    def test_03_analista_nao_publica(self):
        with self.assertRaises(AcessoNegado):self.call('publicar','analista')
        self.assertEqual(self.call('listar')['versoes'],[])
        self.assertTrue(any(r['status']=='negado' and r['perfil']=='analista' for r in self.audit()))
    def test_04_auditor_nao_consulta_dados(self):
        self.publish()
        with self.assertRaises(AcessoNegado):self.call('consultar','auditor')
        self.assertEqual(self.call('verificar','auditor')['integridade'],'OK')
    def test_05_credencial_falsa_negada(self):
        fake=self.base/'invalida.token';fake.write_text('credencial_falsa')
        with self.assertRaises(AcessoNegado):chamar(self.base,'listar',fake)
        self.assertEqual(self.audit()[-1]['status'],'negado')
    def test_06_sem_contatos_no_publicado(self):
        self.publish();data=(self.base/'versoes/v0001/dados.csv').read_text()
        self.assertNotIn('contato_simulado',data);self.assertNotIn('DEMO_ENTIDADE_',data);self.assertNotIn('@example.invalid',data)
        self.assertIn('cliente_pseudo',data)
    def test_07_copia_bruta_cifrada_recuperavel_em_memoria(self):
        self.publish();cipher=(self.base/'versoes/v0001/origem.csv.fernet').read_bytes()
        self.assertNotIn(b'@example.invalid',cipher)
        self.assertIn(b'@example.invalid',decrypt(self.base,cipher))
    def test_08_csv_adulterado_detectado(self):
        self.publish();p=self.base/'versoes/v0001/dados.csv';p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaises(IntegridadeError):self.call('verificar')
        with self.assertRaises(IntegridadeError):self.call('consultar')
    def test_09_manifesto_adulterado_detectado(self):
        self.publish();p=self.base/'versoes/v0001/manifesto.json'
        content=json.loads(p.read_text());content['conteudo']['linhas_publicadas']=999;p.write_text(json.dumps(content))
        with self.assertRaises(IntegridadeError):self.call('verificar')
    def test_10_hmac_protege_mesmo_se_hash_catalogo_for_alterado(self):
        self.publish();p=self.base/'versoes/v0001/manifesto.json'
        content=json.loads(p.read_text());content['conteudo']['linhas_publicadas']=999;p.write_text(json.dumps(content))
        with closing(conectar(self.base)) as c:c.execute('UPDATE versoes SET manifesto_hash=?',(digest(p.read_bytes()),))
        with self.assertRaises(IntegridadeError):self.call('verificar')
    def test_11_duas_versoes_e_comparacao(self):
        self.publish();self.call('simular-lote');r=self.publish()
        self.assertEqual((r['versao'],r['pedidos_concluidos'],r['faturamento_centavos']),('v0002',6,104500))
        diff=self.call('comparar',de='v0001',para='v0002')
        self.assertEqual(diff['adicionados'],[3,7,8]);self.assertEqual(diff['removidos'],[4]);self.assertEqual(diff['alterados'],[2])
        self.assertEqual(diff['delta_faturamento_centavos'],47000);self.assertTrue(diff['alerta_volume'])
    def test_12_restaurar_preserva_origem_e_versoes(self):
        self.publish();self.call('simular-lote');self.publish();self.call('restaurar',versao='v0001')
        self.assertEqual(self.call('consultar')['faturamento_centavos'],57500)
        self.assertEqual(len(self.call('listar')['versoes']),2)
        with closing(conectar(self.base)) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0],8)
    def test_13_engenheiro_nao_restaura(self):
        self.call('publicar','engenheiro')
        with self.assertRaises(AcessoNegado):self.call('restaurar','engenheiro',versao='v0001')
    def test_14_auditoria_tamper_bloqueia_operacoes(self):
        self.publish()
        with closing(conectar(self.base)) as c:c.execute("UPDATE auditoria SET payload='{}' WHERE seq=1")
        with self.assertRaises(IntegridadeError):self.call('listar')
    def test_15_travessia_diretorio_negada(self):
        self.publish()
        for v in ['../../segredos','../v0001','v0001/manifesto.json']:
            with self.assertRaises(ValueError):self.call('verificar',versao=v)
    def test_16_qualidade_invalida_nao_cria_versao(self):
        with closing(conectar(self.base)) as c:c.execute('UPDATE pedidos SET quantidade=-1 WHERE pedido_id=1')
        with self.assertRaises(ValueError):self.publish()
        self.assertEqual(self.call('listar')['versoes'],[])
    def test_17_periodo_vazio_valido(self):
        r=self.call('publicar',inicio='2027-01-01',fim='2027-01-31')
        self.assertEqual(r['pedidos_concluidos'],0);self.assertEqual(self.call('consultar')['faturamento_centavos'],0)
    def test_18_pseudonimo_estavel_e_separado_por_chave(self):
        p=pseudonimo(self.base,'DEMO_ENTIDADE_001')
        self.assertEqual(p,pseudonimo(self.base,'DEMO_ENTIDADE_001'))
        self.assertNotEqual(p,pseudonimo(self.base,'DEMO_ENTIDADE_002'))
        with tempfile.TemporaryDirectory() as temp:
            other=Path(temp);inicializar(other);self.assertNotEqual(p,pseudonimo(other,'DEMO_ENTIDADE_001'))
    def test_19_repetir_publicacao_cria_versao_sem_alterar_anterior(self):
        self.publish();old=(self.base/'versoes/v0001/dados.csv').read_bytes();self.publish()
        self.assertEqual(old,(self.base/'versoes/v0001/dados.csv').read_bytes())
        self.assertEqual(old,(self.base/'versoes/v0002/dados.csv').read_bytes())
    def test_20_logs_nao_contem_segredos_ou_contatos(self):
        self.publish();self.call('consultar');self.call('auditoria')
        text=json.dumps(self.audit())
        for p in (self.base/'segredos').iterdir():self.assertNotIn(p.read_text().strip(),text)
        self.assertNotIn('@example.invalid',text);self.assertNotIn('DEMO_ENTIDADE_',text)
    def test_21_falha_publicacao_nao_altera_ativa(self):
        self.publish()
        with patch('src.snapshot.encrypt',side_effect=RuntimeError('simulada')):
            with self.assertRaises(RuntimeError):self.publish()
        self.assertEqual(self.call('listar')['ativa'],'v0001')
        self.assertFalse((self.base/'versoes/v0002').exists())
    def test_22_snapshots_incluem_governanca_e_consulta(self):
        self.publish()
        with closing(conectar(self.base)) as conn:m,b=conferir(self.base,conn)
        self.assertIn('catalogo.json',b);self.assertIn('consulta.sql',b);self.assertTrue(m['codigo_sha256'])
        self.assertEqual(self.call('auditoria','auditor')['cadeia'],'OK')
    def test_23_delta_aplicado_uma_vez(self):
        self.assertEqual(self.call('simular-lote')['atualizacoes'],5)
        self.assertEqual(self.call('simular-lote')['atualizacoes'],0)
    def test_24_chave_incorreta_recusa_verificacao(self):
        self.publish();p=self.base/'segredos/criptografia.key'
        from cryptography.fernet import Fernet
        p.write_bytes(Fernet.generate_key())
        with self.assertRaises(IntegridadeError):self.call('verificar')

if __name__=='__main__':unittest.main()
