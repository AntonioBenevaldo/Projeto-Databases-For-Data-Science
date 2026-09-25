"""Testes com banco temporario: nao alteram o banco de estudo do usuario."""
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.pipeline import engine, inicializar, extrair, analisar, calcular, comparar, validar_periodo, QUERY

class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.eng = engine(sqlite_path=self.root/'teste.db')
        inicializar(self.eng)
    def tearDown(self):
        self.eng.dispose()
        self.tmp.cleanup()
    def extracao(self, inicio='2026-01-01', fim='2026-03-31', chunk=4, pasta='saida'):
        out=self.root/pasta
        extrair(self.eng,out,inicio,fim,chunk)
        return out
    def test_totais_conferidos_manualmente(self):
        k=analisar(self.extracao())
        self.assertEqual(k['vendas'],10)
        self.assertEqual(k['unidades'],57)
        self.assertEqual(k['faturamento_centavos'],105300)
        self.assertEqual(k['custo_total_centavos'],63000)
        self.assertEqual(k['lucro_bruto_centavos'],42300)
        self.assertEqual(k['ticket_medio_reais'],105.30)
    def test_carga_repetida_nao_duplica(self):
        inicializar(self.eng)
        with self.eng.connect() as c:
            self.assertEqual(c.scalar(text('SELECT COUNT(*) FROM vendas')),12)
            self.assertEqual(c.scalar(text('SELECT COUNT(*) FROM produtos')),4)
    def test_janeiro_e_limites_inclusivos(self):
        k=analisar(self.extracao('2026-01-05','2026-01-15'))
        self.assertEqual(k['vendas'],3)
        self.assertEqual(k['faturamento_centavos'],14300)
    def test_periodo_vazio(self):
        k=analisar(self.extracao('2027-01-01','2027-01-31'))
        self.assertEqual(k['vendas'],0)
        self.assertEqual(k['faturamento_centavos'],0)
        self.assertIsNone(k['ticket_medio_reais'])
    def test_chunks_diferentes_mesmo_resultado(self):
        a=self.extracao(chunk=1,pasta='a'); b=self.extracao(chunk=50,pasta='b')
        self.assertEqual((a/'vendas_extraidas.csv').read_bytes(),(b/'vendas_extraidas.csv').read_bytes())
    def test_parametro_nao_e_executado_como_sql(self):
        with self.eng.connect() as c:
            df=pd.read_sql_query(text(QUERY),c,params={'status':"concluida' OR 1=1 --",'inicio':'2026-01-01','fim':'2026-03-31'})
        self.assertTrue(df.empty)
    def test_restricao_quantidade_no_banco(self):
        with self.assertRaises(IntegrityError):
            with self.eng.begin() as c:
                c.execute(text('UPDATE vendas SET quantidade=0 WHERE venda_id=1'))
    def test_chave_estrangeira_no_banco(self):
        with self.assertRaises(IntegrityError):
            with self.eng.begin() as c:
                c.execute(text('UPDATE vendas SET produto_id=999 WHERE venda_id=1'))
    def test_csv_adulterado_detectado(self):
        out=self.extracao()
        with (out/'vendas_extraidas.csv').open('a') as f: f.write('\n')
        with self.assertRaises(ValueError): analisar(out)
    def test_dados_duplicados_detectados(self):
        df=pd.read_csv(self.extracao()/'vendas_extraidas.csv')
        with self.assertRaises(ValueError): calcular(pd.concat([df,df.iloc[:1]]))
    def test_argumentos_invalidos(self):
        for a,b,c in [('2026-03-01','2026-01-01',4),('2026-01-01','2026-03-31',0),('data','2026-03-31',4)]:
            with self.assertRaises(ValueError): validar_periodo(a,b,c)
    def test_comparador_detecta_divergencia(self):
        a=self.extracao(pasta='a'); b=self.extracao(pasta='b')
        analisar(a); analisar(b); comparar(a,b)
        df=pd.read_csv(b/'resumo_categoria.csv'); df.loc[0,'faturamento_centavos']+=1
        df.to_csv(b/'resumo_categoria.csv',index=False)
        with self.assertRaises(AssertionError): comparar(a,b)

if __name__=='__main__': unittest.main()
