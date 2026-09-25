from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import io
import json
import tempfile
import unittest
import pandas as pd
from sqlalchemy import text
from src.demo import preparar,simular_lote
from src.pipeline import executar,automatizar,FalhaTransitoria
from src.db import bancos,checkpoint
from src.extract import extrair
from src.validate import validar,ErroQualidade
from src.transform import transformar
from src.load import carregar,Concorrencia,FalhaCarga
from src.observe import relatorio

class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='pipeline 15 ')
        self.base=Path(self.tmp.name)
        self.stdout=redirect_stdout(io.StringIO());self.stdout.__enter__()
        preparar(self.base)
    def tearDown(self):
        self.stdout.__exit__(None,None,None);self.tmp.cleanup()
    def run_etl(self,**kwargs):return executar(self.base,espera=0,exportar=False,**kwargs)
    def current(self):
        with bancos(self.base) as (_,dst):return checkpoint(dst)
    def indicadores(self):return relatorio(self.base)[0]
    def facts(self):
        with bancos(self.base) as (_,dst):
            with dst.connect() as c:return pd.read_sql_query(text('SELECT * FROM pedidos_analiticos ORDER BY pedido_id'),c)
    def test_01_primeira_carga_totais(self):
        r=self.run_etl();i=self.indicadores()
        self.assertEqual((r['eventos_lidos'],r['pedidos_alterados'],self.current()),(6,6,6))
        self.assertEqual((i['pedidos_no_destino'],i['pedidos_concluidos'],i['faturamento_centavos'],i['custo_total_centavos'],i['lucro_bruto_centavos']),(6,4,57500,37000,20500))
    def test_02_repeticao_vazia_nao_duplica(self):
        self.run_etl();before=self.facts();r=self.run_etl()
        self.assertEqual((r['eventos_lidos'],r['pedidos_alterados']), (0,0))
        pd.testing.assert_frame_equal(before,self.facts())
    def test_03_delta_atualizacao_e_cancelamento(self):
        self.run_etl();simular_lote(self.base);r=self.run_etl();i=self.indicadores()
        self.assertEqual((r['eventos_lidos'],r['pedidos_alterados'],self.current()),(5,5,11))
        self.assertEqual((i['pedidos_no_destino'],i['pedidos_concluidos'],i['faturamento_centavos'],i['custo_total_centavos'],i['lucro_bruto_centavos']),(8,6,104500,65500,39000))
        f=self.facts().set_index('pedido_id');self.assertEqual(f.loc[4,'status'],'cancelado')
    def test_04_reprocessamento_antigo_nao_desfaz_delta(self):
        self.run_etl();simular_lote(self.base);self.run_etl();before=self.facts()
        r=self.run_etl(desde=0,limite=6)
        self.assertEqual(r['pedidos_alterados'],0);self.assertEqual(self.current(),11)
        pd.testing.assert_frame_equal(before,self.facts())
    def test_05_limite_avanca_so_eventos_lidos(self):
        for expected in [2,4,6]:
            r=self.run_etl(limite=2);self.assertEqual(self.current(),expected)
            self.assertEqual(r['eventos_ainda_pendentes'],6-expected)
    def test_06_retry_transitorio(self):
        r=self.run_etl(falha='transitoria')
        self.assertEqual(r['tentativas'],2);self.assertEqual(self.current(),6)
    def test_07_esgotamento_retry_preserva_cursor(self):
        with self.assertRaises(FalhaTransitoria):self.run_etl(falha='transitoria',tentativas=1)
        self.assertEqual(self.current(),0)
        self.assertEqual(len(list((self.base/'outputs/alertas').glob('*.json'))),1)
    def test_08_erro_qualidade_nao_publica(self):
        with self.assertRaises(ErroQualidade):self.run_etl(falha='qualidade')
        self.assertEqual(self.current(),0);self.assertTrue(self.facts().empty)
        self.assertEqual(self.run_etl()['eventos_lidos'],6)
    def test_09_falha_carga_rollback_do_upsert(self):
        self.run_etl();simular_lote(self.base);before=self.facts()
        with self.assertRaises(FalhaCarga):self.run_etl(falha='carga')
        self.assertEqual(self.current(),6);pd.testing.assert_frame_equal(before,self.facts())
        self.assertEqual(self.run_etl()['eventos_lidos'],5)
    def test_10_erro_to_sql_reverte_resumo_e_checkpoint(self):
        self.run_etl();before=self.indicadores();simular_lote(self.base)
        with patch.object(pd.DataFrame,'to_sql',side_effect=RuntimeError('falha no resumo')):
            with self.assertRaises(RuntimeError):self.run_etl()
        self.assertEqual(self.current(),6);self.assertEqual(before,self.indicadores())
    def test_11_preparar_e_delta_idempotentes(self):
        self.assertEqual(preparar(self.base),0)
        self.assertEqual(simular_lote(self.base),5);self.assertEqual(simular_lote(self.base),0)
        with bancos(self.base) as (src,_):
            with src.connect() as c:self.assertEqual(c.scalar(text('SELECT COUNT(*) FROM eventos')),11)
    def test_12_checkpoint_obsoleto_bloqueado(self):
        self.run_etl()
        with bancos(self.base) as (src,dst):
            raw,_=extrair(src,0,100)
            with self.assertRaises(Concorrencia):carregar(dst,transformar(raw),0,6,'inexistente',{})
    def test_13_dado_tardio_capturado(self):
        self.run_etl();simular_lote(self.base);self.run_etl()
        row=self.facts().set_index('pedido_id').loc[8]
        self.assertEqual(row.data_venda,'2026-01-01');self.assertEqual(row.event_seq,11)
    def test_14_varios_eventos_mesmo_pedido_no_lote(self):
        simular_lote(self.base);r=self.run_etl()
        self.assertEqual((r['eventos_lidos'],r['pedidos_alterados']),(11,8))
        self.assertEqual(self.indicadores()['faturamento_centavos'],104500)
    def test_15_nao_pular_cursor(self):
        with self.assertRaises(ValueError):self.run_etl(desde=99)
        self.assertEqual(self.current(),0)
    def test_16_validacao_rejeita_faixas_e_schema(self):
        with bancos(self.base) as (src,_):raw,_=extrair(src,0,100)
        for col,val in [('quantidade',0),('quantidade',1.5),('status','errado'),('desconto_centavos',999999),('data_venda','2026-99-01')]:
            bad=raw.copy();bad[col]=bad[col].astype(object);bad.loc[0,col]=val
            with self.assertRaises(ErroQualidade):validar(bad)
        with self.assertRaises(ErroQualidade):validar(raw.drop(columns='categoria'))
    def test_17_eventos_duplicados_ou_fora_de_ordem(self):
        with bancos(self.base) as (src,_):raw,_=extrair(src,0,100)
        with self.assertRaises(ErroQualidade):validar(pd.concat([raw,raw.iloc[:1]],ignore_index=True))
        with self.assertRaises(ErroQualidade):validar(raw.iloc[::-1])
    def test_18_automacao_finita(self):
        rs=automatizar(self.base,intervalo=0,repeticoes=2,espera=0,exportar=False)
        self.assertEqual([r['eventos_lidos'] for r in rs],[6,0])
    def test_19_exportacao_e_logs(self):
        r=executar(self.base,espera=0)
        path=self.base/'outputs/execucoes'/r['run_id']
        self.assertTrue((path/'metadados.json').exists());self.assertTrue((path/'relatorio.md').exists())
        events=[json.loads(x)['evento'] for x in (self.base/'outputs/execucoes'/f'{r["run_id"]}.jsonl').read_text().splitlines()]
        self.assertEqual(events,['inicio','extracao','commit_confirmado'])
    def test_20_falha_exportacao_nao_finge_rollback(self):
        with patch('src.pipeline.relatorio',side_effect=OSError('sem permissao no CSV')):
            r=executar(self.base,espera=0)
        self.assertEqual(r['status'],'sucesso');self.assertIn('aviso_exportacao',r)
        self.assertEqual(self.current(),6)
    def test_21_consulta_parametrizada(self):
        with bancos(self.base) as (src,_):
            with self.assertRaises(Exception):extrair(src,0,'1; DROP TABLE eventos')
            with src.connect() as c:self.assertEqual(c.scalar(text('SELECT COUNT(*) FROM eventos')),6)
    def test_22_argumentos_invalidos(self):
        for kwargs in [{'limite':0},{'tentativas':0},{'desde':-1}]:
            with self.assertRaises(ValueError):self.run_etl(**kwargs)

if __name__=='__main__':unittest.main()
