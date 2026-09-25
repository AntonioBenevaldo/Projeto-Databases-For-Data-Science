"""Verificacoes de integridade, temporalidade, leakage e fluxo real."""
from pathlib import Path
import contextlib
import io
import tempfile
import unittest
import sqlite3
import numpy as np
import pandas as pd
import joblib
from src.pipeline import (gerar,ingerir,preprocessar,treinar,avaliar,prever,conferir,
                          ler_json,sha,metricas)
from src.preparacao import (limpar,atributos,dividir_temporal,FEATURES,NUM,CAT,
                           LimitarExtremos)

class ProjetoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='projeto 14 testes ')
        cls.work=Path(cls.tmp.name)
        with contextlib.redirect_stdout(io.StringIO()):
            gerar(cls.work);ingerir(cls.work);preprocessar(cls.work);treinar(cls.work);avaliar(cls.work);prever(cls.work)
        cls.raw=pd.read_csv(cls.work/'data/brutos/pedidos.csv')
        cls.clean,_,cls.quality=limpar(cls.raw)
        cls.parts,cls.gap,cls.split=dividir_temporal(cls.clean)
        cls.prep=joblib.load(cls.work/'modelos/preprocessador.joblib')
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def test_01_contabilidade_da_limpeza(self):
        q=self.quality
        self.assertEqual((q['linhas_brutas'],q['duplicatas_exatas_removidas'],q['registros_rejeitados'],q['linhas_validas']),(1226,20,6,1200))
        self.assertEqual(len(self.clean.pedido_id.unique()),1200)
    def test_02_divisao_sem_sobreposicao(self):
        sets=[set(df.pedido_id) for df in self.parts.values()]+[set(self.gap.pedido_id)]
        self.assertEqual([len(s) for s in sets],[685,205,240,70])
        self.assertEqual(len(set.union(*sets)),1200)
        for i,a in enumerate(sets):
            for b in sets[i+1:]: self.assertFalse(a&b)
    def test_03_rotulos_disponiveis_antes_do_corte(self):
        for nome,corte in [('treino','corte_validacao'),('validacao','corte_teste')]:
            disponivel=pd.to_datetime(self.parts[nome].data_pedido)+pd.Timedelta(days=7)
            self.assertTrue((disponivel<pd.Timestamp(self.split[corte])).all())
    def test_04_features_excluem_futuro_e_alvo(self):
        x=atributos(self.clean)
        self.assertEqual(list(x),FEATURES)
        for c in ['atrasou','dias_entrega_real','pedido_id','data_pedido']: self.assertNotIn(c,x)
        altered=self.clean.copy();altered['atrasou']=1-altered.atrasou;altered['dias_entrega_real']=99999
        pd.testing.assert_frame_equal(x,atributos(altered))
    def test_05_estatisticas_aprendidas_apenas_no_treino(self):
        x=atributos(self.parts['treino'])
        num=self.prep.named_transformers_['numericas']
        upper=np.nanquantile(x[NUM].to_numpy(float),.99,axis=0)
        np.testing.assert_allclose(upper,num.named_steps['limites'].limite_superior_)
        clipped=num.named_steps['limites'].transform(x[NUM])
        med=np.nanmedian(clipped,axis=0)
        np.testing.assert_allclose(med,num.named_steps['mediana'].statistics_)
    def test_06_teste_extremo_nao_reajusta_transformador(self):
        num=self.prep.named_transformers_['numericas']
        before=num.named_steps['limites'].limite_superior_.copy()
        x=atributos(self.parts['teste']).copy();x.loc[:,'valor_pedido']=1e12
        transformed=self.prep.transform(x)
        self.assertTrue(np.isfinite(transformed).all())
        np.testing.assert_array_equal(before,num.named_steps['limites'].limite_superior_)
    def test_07_categoria_futura_nao_aprendida(self):
        enc=self.prep.named_transformers_['categoricas'].named_steps['onehot']
        self.assertNotIn('parceiro',enc.categories_[0])
        x=atributos(self.parts['teste']);x.loc[:,'canal']='categoria_nova'
        self.assertTrue(np.isfinite(self.prep.transform(x)).all())
    def test_08_matrizes_alinhadas_e_sem_nan(self):
        cols=None
        for nome,df in self.parts.items():
            x=pd.read_csv(self.work/f'data/analiticos/X_{nome}.csv')
            y=pd.read_csv(self.work/f'data/analiticos/y_{nome}.csv')
            self.assertEqual(len(x),len(df));self.assertEqual(y.pedido_id.tolist(),df.pedido_id.tolist())
            self.assertTrue(np.isfinite(x.to_numpy()).all())
            if cols is None: cols=list(x)
            self.assertEqual(list(x),cols)
    def test_09_ids_conflitantes_em_quarentena(self):
        raw=self.raw.iloc[:2].copy()
        conflicting=raw.iloc[:1].copy();conflicting['quantidade']=999
        clean,reject,_=limpar(pd.concat([raw,conflicting],ignore_index=True))
        self.assertEqual(len(clean),1);self.assertEqual(len(reject),2)
        self.assertTrue(reject.motivo.str.contains('id_conflitante').all())
    def test_10_metricas_com_resultado_conhecido(self):
        m=metricas([0,0,1,1],[.1,.8,.7,.3])
        self.assertEqual(m['matriz_confusao'],[[1,1],[1,1]])
        self.assertEqual(m['acuracia'],.5);self.assertEqual(m['recall'],.5)
    def test_11_modelo_salvo_equivalente(self):
        b=joblib.load(self.work/'modelos/modelo.joblib')
        p=b['pipeline'].predict_proba(atributos(self.parts['teste']))[:,1]
        saved=pd.read_csv(self.work/'outputs/previsoes_teste.csv')
        np.testing.assert_allclose(p,saved.probabilidade_atraso,rtol=1e-10)
    def test_12_hash_detecta_alteracao(self):
        p=self.work/'outputs/features.json';content=p.read_bytes()
        try:
            p.write_bytes(content+b' ')
            with self.assertRaises(ValueError): conferir(self.work,'preprocessamento')
        finally: p.write_bytes(content)
    def test_13_geracao_reproduzivel(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()): gerar(Path(tmp))
            self.assertEqual(sha(Path(tmp)/'data/brutos/pedidos.csv'),sha(self.work/'data/brutos/pedidos.csv'))
    def test_14_ingestao_repetida_nao_acumula(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()): gerar(p);ingerir(p);ingerir(p)
            with contextlib.closing(sqlite3.connect(p/'data/pedidos.db')) as con:
                count=con.execute('SELECT COUNT(*) FROM pedidos_brutos').fetchone()[0]
            self.assertEqual(count,1226)
    def test_15_novos_exemplos_sem_alvo(self):
        new=pd.read_csv(self.work/'data/brutos/novos_pedidos.csv')
        self.assertNotIn('atrasou',new);self.assertNotIn('dias_entrega_real',new)
        result=pd.read_csv(self.work/'outputs/previsoes_novos.csv')
        self.assertEqual(len(result),5)
        self.assertTrue(result.probabilidade_atraso.between(0,1).all())
    def test_16_origem_alterada_invalida_etapas_futuras(self):
        p=self.work/'data/brutos/pedidos.csv';content=p.read_bytes()
        try:
            p.write_bytes(content+b'\n')
            with self.assertRaises(ValueError): conferir(self.work,'treinamento')
        finally: p.write_bytes(content)
    def test_17_argumento_tamanho_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): gerar(Path(tmp),n=299)
    def test_18_ausencias_continuam_antes_da_imputacao(self):
        self.assertGreater(self.parts['treino'].valor_pedido.isna().sum(),0)
        x=self.prep.transform(atributos(self.parts['treino']))
        self.assertFalse(np.isnan(x).any())

if __name__=='__main__': unittest.main()
