"""
=============================================================================
Implementação do Framework DAR (Dominance Analyses Reduction)
para Processamento de Consultas Skyline em Fluxos de Dados

Baseado no artigo:
  Mohamud et al. (2024). Dominance Analyses Reduction in Skyline Query
  Processing over Data Stream with Data Mining Technique.
  ICICM 2024, Paris, France. ACM.

Técnica de base: Divisão e Conquista (D&C Skyline)
Otimização: Algoritmo Apriori para redução de análises de dominância
=============================================================================
"""

import time
import random
import itertools
from collections import defaultdict


# =============================================================================
# MÓDULO 1 — DEFINIÇÕES FUNDAMENTAIS
# =============================================================================

def domina(oi, oj):
    """
    Verifica se o objeto oi domina oj segundo a definição de Pareto.
    oi domina oj se:
      - oi é <= oj em TODAS as dimensões, E
      - oi é <  oj em PELO MENOS UMA dimensão.
    Assume-se que valores menores são preferíveis (ex: menor preço, menor distância).
    """
    pelo_menos_um_menor = False
    for k in range(len(oi)):
        if oi[k] > oj[k]:
            return False          # oi é pior em alguma dimensão → não domina
        if oi[k] < oj[k]:
            pelo_menos_um_menor = True
    return pelo_menos_um_menor


def relacao_dominancia(oi, oj):
    """
    Retorna o relacionamento de dominância entre oi e oj:
      'oi'  → oi domina oj
      'oj'  → oj domina oi
      'nenhum' → nenhum domina o outro (incomparáveis)
    """
    if domina(oi, oj):
        return 'oi'
    elif domina(oj, oi):
        return 'oj'
    else:
        return 'nenhum'


# =============================================================================
# MÓDULO 2 — ALGORITMO SKYLINE CONVENCIONAL (CSA - Block Nested Loop)
# =============================================================================

class SkylineConvencional:
    """
    Algoritmo Skyline Convencional (CSA).
    Realiza todas as comparações par-a-par sem nenhuma otimização.
    Complexidade: O(n²) comparações de objetos.
    """

    def __init__(self):
        self.total_comparacoes_objetos = 0
        self.total_comparacoes_dimensoes = 0

    def calcular(self, objetos):
        """
        Calcula o skyline de uma lista de objetos.
        Retorna a lista de objetos skyline.
        """
        if not objetos:
            return []

        n = len(objetos)
        m = len(objetos[0])
        dominado = [False] * n

        for i in range(n):
            for j in range(n):
                if i == j or dominado[i]:
                    continue
                self.total_comparacoes_objetos += 1
                # Conta comparações por dimensão
                for k in range(m):
                    self.total_comparacoes_dimensoes += 1
                    if objetos[i][k] > objetos[j][k]:
                        break  # oi não domina oj
                else:
                    # Verificação completa de dominância
                    if domina(objetos[j], objetos[i]):
                        dominado[i] = True
                        break

        return [objetos[i] for i in range(n) if not dominado[i]]

    def resetar_contadores(self):
        self.total_comparacoes_objetos = 0
        self.total_comparacoes_dimensoes = 0


# =============================================================================
# MÓDULO 3 — ALGORITMO D&C SKYLINE (BASE DO DAR)
# =============================================================================

class SkylineDivideConquista:
    """
    Algoritmo Skyline por Divisão e Conquista.

    Fases:
      1. DIVISÃO:   Divide o conjunto de objetos recursivamente ao meio.
      2. CONQUISTA: Calcula o skyline local de cada subconjunto.
      3. COMBINAÇÃO: Funde os skylines locais, eliminando objetos dominados.

    É exatamente na fase de COMBINAÇÃO que ocorrem as análises de dominância
    que o framework DAR visa otimizar.
    """

    def __init__(self):
        self.total_comparacoes_objetos = 0
        self.total_comparacoes_dimensoes = 0
        self.nivel_recursao = 0

    def calcular(self, objetos):
        """Ponto de entrada público."""
        if not objetos:
            return []
        return self._dividir_e_conquistar(objetos)

    def _dividir_e_conquistar(self, objetos):
        """Implementação recursiva de D&C para skyline."""
        n = len(objetos)

        # CASO BASE: subconjunto com 1 objeto → já é skyline local
        if n == 1:
            return [objetos[0]]

        # ── DIVISÃO ──────────────────────────────────────────────────────────
        meio = n // 2
        esquerda = objetos[:meio]
        direita = objetos[meio:]

        # ── CONQUISTA ─────────────────────────────────────────────────────────
        skyline_esq = self._dividir_e_conquistar(esquerda)
        skyline_dir = self._dividir_e_conquistar(direita)

        # ── COMBINAÇÃO ────────────────────────────────────────────────────────
        return self._combinar(skyline_esq, skyline_dir)

    def _combinar(self, skyline_a, skyline_b):
        """
        Fase de COMBINAÇÃO: funde dois skylines locais.
        Remove de skyline_b qualquer ponto dominado por algum ponto de skyline_a,
        e vice-versa. Aqui ocorrem as análises de dominância redundantes
        que o DAR irá otimizar.
        """
        resultado = list(skyline_a)

        for obj_b in skyline_b:
            dominado = False
            for obj_a in skyline_a:
                self.total_comparacoes_objetos += 1
                self.total_comparacoes_dimensoes += len(obj_a)
                if domina(obj_a, obj_b):
                    dominado = True
                    break
            if not dominado:
                # Verificar se obj_b domina algum de skyline_a
                resultado = [
                    obj_a for obj_a in resultado
                    if not domina(obj_b, obj_a)
                ]
                resultado.append(obj_b)

        return resultado

    def resetar_contadores(self):
        self.total_comparacoes_objetos = 0
        self.total_comparacoes_dimensoes = 0


# =============================================================================
# MÓDULO 4 — ALGORITMO APRIORI (identificação de análises frequentes)
# =============================================================================

class Apriori:
    """
    Implementação do Algoritmo Apriori para identificar pares de objetos
    cujas análises de dominância ocorrem frequentemente no fluxo de dados.

    Entrada:  DA&RL — lista de análises de dominância realizadas anteriormente
              Formato: [(chave_par, resultado), ...]
    Saída:    FDA&RL — dicionário com pares frequentes e seus resultados
              Formato: {chave_par: resultado}
    """

    def __init__(self, min_support=2, min_lift=1.0):
        self.min_support = min_support   # suporte mínimo (nº de ocorrências)
        self.min_lift    = min_lift      # lift mínimo para associação forte

    def executar(self, da_rl):
        """
        Executa o Apriori sobre a lista DA&RL e retorna o FDA&RL.

        da_rl: lista de tuplas (chave_par, resultado)
               chave_par = tupla ordenada de dois objetos (como tuplas)
        """
        if not da_rl:
            return {}

        total = len(da_rl)

        # ── Passo 1: contagem de suporte por objeto individual (C1) ──────────
        contagem_obj = defaultdict(int)
        for par, _ in da_rl:
            contagem_obj[par[0]] += 1
            contagem_obj[par[1]] += 1

        # Poda: remover objetos abaixo do suporte mínimo
        L1 = {obj for obj, cnt in contagem_obj.items() if cnt >= self.min_support}

        # ── Passo 2: contagem de suporte por par de objetos (C2) ─────────────
        contagem_par = defaultdict(int)
        resultado_par = {}

        for par, resultado in da_rl:
            if par[0] in L1 and par[1] in L1:
                contagem_par[par] += 1
                resultado_par[par] = resultado  # último resultado visto (são iguais por def.)

        # Poda: remover pares abaixo do suporte mínimo
        L2 = {par: cnt for par, cnt in contagem_par.items() if cnt >= self.min_support}

        # ── Passo 3: calcular suporte, confiança e lift; filtrar por lift ────
        fda_rl = {}
        suporte_obj = {obj: cnt / total for obj, cnt in contagem_obj.items()}

        for par, cnt in L2.items():
            suporte = cnt / total
            confianca = cnt / contagem_obj[par[0]] if contagem_obj[par[0]] > 0 else 0
            sp_a = suporte_obj.get(par[0], 0)
            sp_b = suporte_obj.get(par[1], 0)
            lift = suporte / (sp_a * sp_b) if (sp_a * sp_b) > 0 else 0

            if lift > self.min_lift:
                fda_rl[par] = resultado_par[par]

        return fda_rl


# =============================================================================
# MÓDULO 5 — FRAMEWORK DAR COMPLETO
# =============================================================================

class FrameworkDAR:
    """
    Framework DAR (Dominance Analyses Reduction).

    Integra o D&C Skyline com o cache FDA&RL gerado pelo Apriori,
    evitando análises de dominância redundantes em janelas deslizantes.

    Fluxo:
      [Fase 1] Apriori → identifica pares frequentes → gera FDA&RL
      [Fase 2] D&C Skyline com FDA&RL → consulta análises já conhecidas
                                        antes de recomputar
    """

    def __init__(self, min_support=2, min_lift=1.0):
        self.apriori = Apriori(min_support, min_lift)
        self.fda_rl  = {}      # cache de análises frequentes
        self.da_rl   = []      # histórico de análises realizadas

        self.total_comparacoes_objetos    = 0
        self.total_comparacoes_dimensoes  = 0
        self.analises_evitadas            = 0

    # ── Utilitários ──────────────────────────────────────────────────────────

    def _chave_par(self, oi, oj):
        """Chave canônica (ordem não importa — propriedade simétrica)."""
        a, b = tuple(oi), tuple(oj)
        return (a, b) if a <= b else (b, a)

    def _analisar_dominancia(self, oi, oj):
        """
        Realiza ou recupera a análise de dominância entre oi e oj.
        Se o par estiver no FDA&RL, usa o resultado cacheado (evita recomputa).
        """
        chave = self._chave_par(oi, oj)

        if chave in self.fda_rl:
            self.analises_evitadas += 1
            return self.fda_rl[chave]

        # Análise efetiva
        self.total_comparacoes_objetos += 1
        self.total_comparacoes_dimensoes += len(oi)
        resultado = relacao_dominancia(oi, oj)

        # Registrar no histórico para futuras rodadas do Apriori
        self.da_rl.append((chave, resultado))
        return resultado

    # ── Fase 1: treinar Apriori ───────────────────────────────────────────────

    def treinar_apriori(self, janelas_historico):
        """
        Recebe janelas anteriores de dados, executa skyline convencional
        para preencher o DA&RL, depois roda o Apriori para gerar o FDA&RL.
        """
        for janela in janelas_historico:
            objetos = list(janela)
            for i in range(len(objetos)):
                for j in range(i + 1, len(objetos)):
                    chave = self._chave_par(objetos[i], objetos[j])
                    res = relacao_dominancia(objetos[i], objetos[j])
                    self.da_rl.append((chave, res))

        self.fda_rl = self.apriori.executar(self.da_rl)
        print(f"  [Apriori] DA&RL: {len(self.da_rl)} análises | "
              f"FDA&RL: {len(self.fda_rl)} pares frequentes")

    # ── Fase 2: D&C com FDA&RL ───────────────────────────────────────────────

    def calcular_skyline(self, objetos):
        """Calcula o skyline usando D&C com cache FDA&RL."""
        if not objetos:
            return []
        return self._dc_com_cache(objetos)

    def _dc_com_cache(self, objetos):
        n = len(objetos)
        if n == 1:
            return [objetos[0]]

        meio = n // 2
        sky_esq = self._dc_com_cache(objetos[:meio])
        sky_dir = self._dc_com_cache(objetos[meio:])
        return self._combinar_com_cache(sky_esq, sky_dir)

    def _combinar_com_cache(self, skyline_a, skyline_b):
        """Combinação D&C com consulta ao FDA&RL antes de recalcular."""
        resultado = list(skyline_a)

        for obj_b in skyline_b:
            dominado = False
            for obj_a in skyline_a:
                rel = self._analisar_dominancia(obj_a, obj_b)
                if rel == 'oi':   # obj_a domina obj_b
                    dominado = True
                    break
            if not dominado:
                resultado = [
                    obj_a for obj_a in resultado
                    if self._analisar_dominancia(obj_b, obj_a) != 'oi'
                ]
                resultado.append(obj_b)

        return resultado

    def resetar_contadores(self):
        self.total_comparacoes_objetos   = 0
        self.total_comparacoes_dimensoes = 0
        self.analises_evitadas           = 0


# =============================================================================
# MÓDULO 6 — JANELAS DESLIZANTES (Sliding Windows)
# =============================================================================

class JanelaDeslizante:
    """
    Simula o processamento de janelas deslizantes sobre um fluxo de dados.
    Cada objeto tem um timestamp de chegada (t_arr).
    """

    def __init__(self, range_janela, slide):
        self.range_janela = range_janela   # tamanho da janela em unidades de tempo
        self.slide = slide                  # passo de deslizamento

    def gerar_janelas(self, stream, t_inicio=0, t_fim=None):
        """
        Gera janelas a partir do stream.
        stream: lista de (objeto, timestamp)
        Retorna lista de listas de objetos por janela.
        """
        if t_fim is None:
            t_fim = max(t for _, t in stream)

        janelas = []
        t = t_inicio
        while t + self.range_janela <= t_fim + self.slide:
            lb = t
            ub = t + self.range_janela
            objetos_janela = [obj for obj, ts in stream if lb <= ts < ub]
            if objetos_janela:
                janelas.append(objetos_janela)
            t += self.slide

        return janelas


# =============================================================================
# MÓDULO 7 — GERAÇÃO DE DADOS SINTÉTICOS
# =============================================================================

def gerar_stream(n_objetos, n_dims, perc_duplicatas=0.5, seed=42):
    """
    Gera um fluxo de dados sintético com objetos aleatórios e duplicatas.
    Retorna lista de (objeto_tuple, timestamp).
    """
    random.seed(seed)
    objetos_unicos = [
        tuple(random.randint(1, 100) for _ in range(n_dims))
        for _ in range(int(n_objetos * (1 - perc_duplicatas)))
    ]
    todos = list(objetos_unicos)
    # Adicionar duplicatas (objetos que reaparecem no stream)
    n_dup = n_objetos - len(objetos_unicos)
    todos += random.choices(objetos_unicos, k=n_dup)
    random.shuffle(todos)

    stream = [(obj, i + 1) for i, obj in enumerate(todos)]
    return stream


# =============================================================================
# MÓDULO 8 — EXPERIMENTOS E COMPARAÇÕES
# =============================================================================

def executar_experimento(n_objetos, n_dims, perc_dup=0.5, verbose=True):
    """
    Executa um experimento comparando CSA, D&C puro e DAR,
    medindo comparações e tempo de execução.
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"  Experimento: n={n_objetos} objetos | d={n_dims} dims | dup={perc_dup*100:.0f}%")
        print(f"{'='*60}")

    stream = gerar_stream(n_objetos, n_dims, perc_dup)

    # Janelas deslizantes: range=40, slide=20 → sobreposição de 50%
    jd = JanelaDeslizante(range_janela=40, slide=20)
    janelas = jd.gerar_janelas(stream, t_inicio=0, t_fim=n_objetos)

    if not janelas:
        return None

    # Separar janelas de treino (históricas) e de teste
    janelas_treino = janelas[:max(1, len(janelas)//2)]
    janelas_teste  = janelas[len(janelas)//2:]

    resultados = {}

    # ── CSA ──────────────────────────────────────────────────────────────────
    csa = SkylineConvencional()
    t0 = time.perf_counter()
    for janela in janelas_teste:
        csa.calcular(janela)
    tempo_csa = time.perf_counter() - t0
    resultados['CSA'] = {
        'comp_obj': csa.total_comparacoes_objetos,
        'comp_dim': csa.total_comparacoes_dimensoes,
        'tempo':    tempo_csa
    }

    # ── D&C Puro ─────────────────────────────────────────────────────────────
    dc = SkylineDivideConquista()
    t0 = time.perf_counter()
    for janela in janelas_teste:
        dc.calcular(janela)
    tempo_dc = time.perf_counter() - t0
    resultados['D&C'] = {
        'comp_obj': dc.total_comparacoes_objetos,
        'comp_dim': dc.total_comparacoes_dimensoes,
        'tempo':    tempo_dc
    }

    # ── DAR (D&C + Apriori + FDA&RL) ─────────────────────────────────────────
    dar = FrameworkDAR(min_support=2, min_lift=1.0)
    if verbose:
        print("\n  [Fase 1 - Apriori] Treinando com janelas históricas...")
    dar.treinar_apriori(janelas_treino)

    t0 = time.perf_counter()
    for janela in janelas_teste:
        dar.calcular_skyline(janela)
    tempo_dar = time.perf_counter() - t0
    resultados['DAR'] = {
        'comp_obj':        dar.total_comparacoes_objetos,
        'comp_dim':        dar.total_comparacoes_dimensoes,
        'tempo':           tempo_dar,
        'analises_evit':   dar.analises_evitadas,
        'fda_rl_size':     len(dar.fda_rl)
    }

    if verbose:
        _imprimir_resultados(resultados, n_dims)

    return resultados


def _imprimir_resultados(resultados, n_dims):
    print("\n  ── RESULTADOS ──────────────────────────────────────────")
    print(f"  {'Métrica':<35} {'CSA':>10} {'D&C':>10} {'DAR':>10}")
    print(f"  {'-'*65}")

    for metrica, chave in [
        ("Comparações (objetos)",  'comp_obj'),
        ("Comparações (dimensões)",'comp_dim'),
        ("Tempo (s)",              'tempo'),
    ]:
        vals = {k: resultados[k][chave] for k in ['CSA','D&C','DAR']}
        fmt = ".4f" if chave == 'tempo' else "d"
        print(f"  {metrica:<35} "
              f"{vals['CSA']:>10{fmt}} "
              f"{vals['D&C']:>10{fmt}} "
              f"{vals['DAR']:>10{fmt}}")

    dar = resultados['DAR']
    print(f"\n  Análises de dominância evitadas (DAR): {dar['analises_evit']}")
    print(f"  Pares no FDA&RL: {dar['fda_rl_size']}")

    csa_comp = resultados['CSA']['comp_obj']
    dar_comp = resultados['DAR']['comp_obj']
    if csa_comp > 0:
        red = (1 - dar_comp / csa_comp) * 100
        print(f"  Redução de comparações DAR vs CSA: {red:.1f}%")

    csa_t = resultados['CSA']['tempo']
    dar_t = resultados['DAR']['tempo']
    if csa_t > 0:
        red_t = (1 - dar_t / csa_t) * 100
        print(f"  Redução de tempo DAR vs CSA: {red_t:.1f}%")


# =============================================================================
# MÓDULO 9 — DEMONSTRAÇÃO COM EXEMPLO DO ARTIGO
# =============================================================================

def demo_exemplo_artigo():
    """
    Reproduz o exemplo da Tabela 1 do artigo original.
    Objetos: apartamentos com atributos (preço, distância).
    Skyline esperado: {o1, o3, o5, o6, o7}
    """
    print("\n" + "="*60)
    print("  DEMONSTRAÇÃO — Exemplo da Tabela 1 do Artigo")
    print("="*60)

    # (preço, distância) — menores valores são melhores
    objetos_stream = [
        ((200, 0.5),  1),   # o1
        ((150, 2),    2),   # o2
        ((25,  15),   3),   # o3
        ((125, 3.5),  4),   # o4
        ((100, 5),    6),   # o5
        ((75,  8),    7),   # o6
        ((115, 2),    8),   # o7
        ((176, 4),   10),   # o8
        ((25,  15),  12),   # o3 (reaparece)
        ((60,  15),  14),   # o9
        ((186, 2),   16),   # o10
        ((100, 5),   18),   # o5 (reaparece)
    ]

    # Janela w1: t=[0,10], w2: t=[7,20]
    w1 = [obj for obj, ts in objetos_stream if 0 <= ts <= 10]
    w2 = [obj for obj, ts in objetos_stream if 7 <= ts <= 20]

    print(f"\n  Janela w1 ({len(w1)} objetos): {w1}")
    print(f"  Janela w2 ({len(w2)} objetos): {w2}")

    # D&C Skyline
    dc = SkylineDivideConquista()
    sky_w1 = dc.calcular(w1)
    sky_w2 = dc.calcular(w2)

    print(f"\n  Skyline w1 (D&C): {sky_w1}")
    print(f"  Skyline w2 (D&C): {sky_w2}")
    print(f"  Comparações realizadas (objetos): {dc.total_comparacoes_objetos}")

    # DAR
    dar = FrameworkDAR(min_support=2, min_lift=1.0)
    dar.treinar_apriori([w1])   # treina com w1

    print(f"\n  [DAR] Calculando skyline de w2 com FDA&RL...")
    sky_w2_dar = dar.calcular_skyline(w2)
    print(f"  Skyline w2 (DAR): {sky_w2_dar}")
    print(f"  Comparações realizadas (objetos): {dar.total_comparacoes_objetos}")
    print(f"  Análises evitadas pelo cache:     {dar.analises_evitadas}")

    print(f"\n  Verificação: skylines D&C e DAR são iguais? "
          f"{'✓ SIM' if sorted(sky_w2) == sorted(sky_w2_dar) else '✗ NÃO'}")


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("  DAR Framework — Implementação em Python")
    print("  Técnica base: Divisão e Conquista (D&C Skyline)")
    print("  Otimização: Apriori (FDA&RL)")
    print("="*60)

    # 1. Demonstração com o exemplo do artigo
    demo_exemplo_artigo()

    # 2. Experimentos com dados sintéticos
    print("\n\n  EXPERIMENTOS COM DADOS SINTÉTICOS")

    # Variando número de objetos (|d| = 4 fixo)
    print("\n  [A] Variando número de objetos (|d|=4 fixo)")
    for n in [50, 100, 200, 500]:
        executar_experimento(n_objetos=n, n_dims=4, perc_dup=0.5)

    # Variando número de dimensões (|n| = 200 fixo)
    print("\n  [B] Variando número de dimensões (|n|=200 fixo)")
    for d in [2, 4, 6, 8, 10]:
        executar_experimento(n_objetos=200, n_dims=d, perc_dup=0.5)

    print("\n\n  Execução concluída.")