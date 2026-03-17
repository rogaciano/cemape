"""
Serviço de cálculo de custas e honorários para câmaras de arbitragem/mediação.

Responsabilidade única: dado um conjunto de parâmetros de entrada, retorna
o detalhamento completo dos valores a pagar, sem qualquer lógica de apresentação.

Os valores não estão hardcoded — são carregados de TabelaCustas/FaixaCustas/
ConfiguracaoCalculadora, que podem ser editados pelo painel administrativo.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from ..models import (
    TabelaCustas, FaixaCustas, ConfiguracaoCalculadora,
    TipoTaxa, MetodoCalculo,
)


# ---------------------------------------------------------------------------
# DTOs de entrada e saída
# ---------------------------------------------------------------------------

@dataclass
class EntradaCalculadora:
    valor_demanda: Decimal
    tipo_procedimento: str                  # 'ARBITRAGEM' | 'MEDIACAO'
    quantidade_arbitros: int = 1            # 1 (árbitro único) ou 3 (tribunal)
    procedimento_expedito: bool = False     # só Arbitragem
    horas_trabalhadas: Optional[Decimal] = None   # só Mediação
    quantidade_mediadores: int = 1          # só Mediação
    instituicao: str = 'CEMAPE'


@dataclass
class ItemHonorario:
    descricao: str
    valor: Decimal


@dataclass
class ResultadoCalculadora:
    taxa_registro: Decimal
    taxa_administracao: Decimal
    honorarios_individuais: list = field(default_factory=list)   # list[ItemHonorario]
    total_honorarios: Decimal = Decimal('0')
    custo_total: Decimal = Decimal('0')
    observacoes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _moeda(valor: Decimal) -> Decimal:
    """Arredonda para 2 casas, seguindo regra HALF_UP."""
    return valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _encontrar_faixa(vd: Decimal, faixas) -> Optional[FaixaCustas]:
    """
    Retorna a primeira faixa em que VD está compreendido.
    A última faixa com demanda_max=None cobre valores acima do último limite.
    """
    for faixa in faixas:
        limite_sup = faixa.demanda_max
        if limite_sup is None or vd <= limite_sup:
            return faixa
    return None


def _calcular_horas_faturadas(horas_trabalhadas: Decimal, minimo: int) -> Decimal:
    """
    Aplica arredondamento fracionado CEMAPE Mediação:
      - Fração ≤ 30 min → cobra meia hora
      - Fração > 30 min → cobra hora cheia
    Garante mínimo de `minimo` horas.
    """
    horas_int = int(horas_trabalhadas)
    minutos = (horas_trabalhadas - horas_int) * 60

    if minutos == 0:
        arredondado = Decimal(horas_int)
    elif minutos <= 30:
        arredondado = Decimal(horas_int) + Decimal('0.5')
    else:
        arredondado = Decimal(horas_int + 1)

    return max(arredondado, Decimal(minimo))


# ---------------------------------------------------------------------------
# Calculadores por método
# ---------------------------------------------------------------------------

class _Calculador:
    """Agrupa os métodos de cálculo primitivos, reutilizáveis por qualquer instituição."""

    @staticmethod
    def percentual_demanda(vd: Decimal, pct: Decimal, piso: Decimal, teto: Decimal) -> Decimal:
        valor = vd * (pct / 100)
        return _moeda(max(piso, min(teto, valor)))

    @staticmethod
    def fixo(valor: Decimal) -> Decimal:
        return _moeda(valor)

    @staticmethod
    def interpolacao(vd: Decimal, faixa: FaixaCustas) -> Decimal:
        """
        V = Vmin + ((VD - FCmin) / (FCmax - FCmin)) * (Vmax - Vmin)
        Quando VD == demanda_min da faixa (primeira faixa fixa), retorna valor_min.
        """
        fc_min = faixa.demanda_min
        fc_max = faixa.demanda_max
        v_min = faixa.valor_min
        v_max = faixa.valor_max

        if fc_max is None or fc_min == fc_max:
            return _moeda(v_min)

        resultado = v_min + ((vd - fc_min) / (fc_max - fc_min)) * (v_max - v_min)
        return _moeda(resultado)

    @staticmethod
    def base_mais_pct(vd: Decimal, faixa: FaixaCustas) -> Decimal:
        """
        resultado = valor_base + (VD - demanda_min) * pct_excedente / 100
        Se a faixa definir valor_teto_faixa, aplica como teto.
        """
        excedente = vd - faixa.demanda_min
        resultado = faixa.valor_base + excedente * (faixa.pct_excedente / 100)
        if faixa.valor_teto_faixa is not None:
            resultado = min(resultado, faixa.valor_teto_faixa)
        return _moeda(resultado)

    @staticmethod
    def faixa_fixa(faixa: FaixaCustas) -> Decimal:
        return _moeda(faixa.valor_fixo)

    @staticmethod
    def hora_trabalhada(faixa: FaixaCustas, horas_faturadas: Decimal) -> Decimal:
        return _moeda(faixa.valor_fixo * horas_faturadas)


# ---------------------------------------------------------------------------
# Classe principal do serviço
# ---------------------------------------------------------------------------

class CalculadoraService:
    """
    Ponto de entrada único. Delega para o calculador correto com base em
    (instituicao, tipo_procedimento).
    """

    def calcular(self, entrada: EntradaCalculadora) -> ResultadoCalculadora:
        calculadores = {
            'ARBITRAGEM': self._cemape_arbitragem,
            'MEDIACAO':   self._cemape_mediacao,
        }
        handler = calculadores.get(entrada.tipo_procedimento.upper())
        if handler is None:
            raise ValueError(f'Procedimento não suportado: {entrada.tipo_procedimento}')
        return handler(entrada)

    # ------------------------------------------------------------------
    # Helpers de acesso ao banco
    # ------------------------------------------------------------------

    def _cfg(self, instituicao: str, procedimento: str, chave: str) -> Decimal:
        obj = ConfiguracaoCalculadora.objects.get(
            instituicao=instituicao,
            tipo_procedimento=procedimento,
            chave=chave,
            ativa=True,
        )
        return obj.valor

    def _tabela(self, instituicao: str, procedimento: str, tipo_taxa: str):
        return (
            TabelaCustas.objects
            .prefetch_related('faixas')
            .get(
                instituicao=instituicao,
                tipo_procedimento=procedimento,
                tipo_taxa=tipo_taxa,
                ativa=True,
            )
        )

    def _faixas(self, tabela: TabelaCustas):
        return tabela.faixas.order_by('ordem')

    def _calcular_tabela(self, vd: Decimal, tabela: TabelaCustas) -> Decimal:
        faixas = self._faixas(tabela)
        faixa = _encontrar_faixa(vd, faixas)
        if faixa is None:
            raise ValueError(f'VD R$ {vd:,.2f} fora do alcance da tabela: {tabela}')

        metodo = tabela.metodo_calculo
        if metodo == MetodoCalculo.INTERPOLACAO:
            return _Calculador.interpolacao(vd, faixa)
        if metodo == MetodoCalculo.BASE_MAIS_PCT:
            return _Calculador.base_mais_pct(vd, faixa)
        if metodo == MetodoCalculo.FAIXA_FIXA:
            return _Calculador.faixa_fixa(faixa)
        raise ValueError(f'Método {metodo} não tratado em _calcular_tabela')

    # ------------------------------------------------------------------
    # CEMAPE — Arbitragem
    # ------------------------------------------------------------------

    def _cemape_arbitragem(self, e: EntradaCalculadora) -> ResultadoCalculadora:
        vd = e.valor_demanda
        inst, proc = 'CEMAPE', 'ARBITRAGEM'

        # Taxa de Registro
        pct   = self._cfg(inst, proc, 'taxa_registro_pct')
        piso  = self._cfg(inst, proc, 'taxa_registro_piso')
        teto  = self._cfg(inst, proc, 'taxa_registro_teto')
        taxa_registro = _Calculador.percentual_demanda(vd, pct, piso, teto)

        # Taxa de Administração
        tab_admin = self._tabela(inst, proc, TipoTaxa.ADMINISTRACAO)
        taxa_admin = self._calcular_tabela(vd, tab_admin)

        # Honorários — valor base por árbitro
        tab_hon = self._tabela(inst, proc, TipoTaxa.HONORARIOS)
        honorario_base = self._calcular_tabela(vd, tab_hon)

        # Modificadores
        itens: list[ItemHonorario] = []
        obs: list[str] = []

        if e.procedimento_expedito:
            # Árbitro único com desconto de 20% sobre o valor base
            desconto_pct = self._cfg(inst, proc, 'expedita_desconto_pct')
            valor = _moeda(honorario_base * (1 - desconto_pct / 100))
            itens.append(ItemHonorario('Árbitro Único (Expedita, desconto 20%)', valor))
            obs.append('Procedimento Expedito: honorários com desconto de 20% sobre o valor base.')

        elif e.quantidade_arbitros == 1:
            adicional_pct = self._cfg(inst, proc, 'arbitro_unico_adicional_pct')
            valor = _moeda(honorario_base * (1 + adicional_pct / 100))
            itens.append(ItemHonorario(f'Árbitro Único (+{int(adicional_pct)}% sobre a base)', valor))

        else:
            # Tribunal de 3 árbitros
            presidente_pct = self._cfg(inst, proc, 'tribunal_presidente_adicional_pct')
            valor_co = honorario_base
            valor_pres = _moeda(honorario_base * (1 + presidente_pct / 100))
            itens.append(ItemHonorario('Co-árbitro 1', valor_co))
            itens.append(ItemHonorario('Co-árbitro 2', valor_co))
            itens.append(ItemHonorario(f'Árbitro Presidente (+{int(presidente_pct)}%)', valor_pres))

        total_hon = _moeda(sum(i.valor for i in itens))
        custo_total = _moeda(taxa_registro + taxa_admin + total_hon)

        return ResultadoCalculadora(
            taxa_registro=taxa_registro,
            taxa_administracao=taxa_admin,
            honorarios_individuais=itens,
            total_honorarios=total_hon,
            custo_total=custo_total,
            observacoes=obs,
        )

    # ------------------------------------------------------------------
    # CEMAPE — Mediação
    # ------------------------------------------------------------------

    def _cemape_mediacao(self, e: EntradaCalculadora) -> ResultadoCalculadora:
        vd = e.valor_demanda
        inst, proc = 'CEMAPE', 'MEDIACAO'

        # Taxa de Registro
        pct  = self._cfg(inst, proc, 'taxa_registro_pct')
        piso = self._cfg(inst, proc, 'taxa_registro_piso')
        teto = self._cfg(inst, proc, 'taxa_registro_teto')
        taxa_registro = _Calculador.percentual_demanda(vd, pct, piso, teto)

        # Taxa de Administração (valor fixo por faixa)
        tab_admin = self._tabela(inst, proc, TipoTaxa.ADMINISTRACAO)
        taxa_admin = self._calcular_tabela(vd, tab_admin)

        # Honorários (por hora trabalhada)
        tab_hon = self._tabela(inst, proc, TipoTaxa.HONORARIOS)
        faixas = self._faixas(tab_hon)
        faixa = _encontrar_faixa(vd, faixas)
        if faixa is None:
            raise ValueError(f'VD R$ {vd:,.2f} fora do alcance da tabela de honorários mediação')

        min_horas = int(self._cfg(inst, proc, 'mediacao_horas_minimas'))
        horas_in  = e.horas_trabalhadas or Decimal(min_horas)
        horas_fat = _calcular_horas_faturadas(horas_in, min_horas)
        valor_hora = faixa.valor_fixo
        total_hon  = _Calculador.hora_trabalhada(faixa, horas_fat)

        obs = []
        if horas_fat > horas_in:
            obs.append(
                f'Mínimo de {min_horas} horas aplicado. '
                f'Horas trabalhadas: {horas_in}h → faturadas: {horas_fat}h.'
            )

        qtd = max(1, e.quantidade_mediadores or 1)
        hon_por_mediador = total_hon
        itens = []
        for i in range(1, qtd + 1):
            label = f'Mediador {i}' if qtd > 1 else 'Mediador'
            itens.append(ItemHonorario(
                f'{label} ({horas_fat}h × R$ {valor_hora:,.2f}/h)',
                hon_por_mediador,
            ))

        total_hon = _moeda(hon_por_mediador * qtd)
        if qtd > 1:
            obs.append(f'{qtd} mediadores × R$ {hon_por_mediador:,.2f} cada = R$ {total_hon:,.2f} total de honorários.')

        custo_total = _moeda(taxa_registro + taxa_admin + total_hon)

        return ResultadoCalculadora(
            taxa_registro=taxa_registro,
            taxa_administracao=taxa_admin,
            honorarios_individuais=itens,
            total_honorarios=total_hon,
            custo_total=custo_total,
            observacoes=obs,
        )

