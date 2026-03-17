"""
Modelos editáveis pelo admin para as tabelas de custas e honorários
do CEMAPE e da CAMARB. Nenhum valor de taxa está hardcoded no código.
"""
from django.db import models
from apps.core.models import BaseModel


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class Instituicao(models.TextChoices):
    CEMAPE = 'CEMAPE', 'CEMAPE'
    CAMARB = 'CAMARB', 'CAMARB'


class TipoProcedimento(models.TextChoices):
    ARBITRAGEM = 'ARBITRAGEM', 'Arbitragem'
    MEDIACAO = 'MEDIACAO', 'Mediação'


class TipoTaxa(models.TextChoices):
    REGISTRO = 'REGISTRO', 'Taxa de Registro'
    ADMINISTRACAO = 'ADMINISTRACAO', 'Taxa de Administração'
    HONORARIOS = 'HONORARIOS', 'Honorários dos Árbitros/Mediadores'


class MetodoCalculo(models.TextChoices):
    """
    PERCENTUAL_DEMANDA : taxa_registro = pct * VD, com piso/teto (CEMAPE)
    FIXO               : valor único independente do VD (registro CAMARB)
    INTERPOLACAO       : fórmula V=Vmin+(VD-FCmin)/(FCmax-FCmin)*(Vmax-Vmin) (CEMAPE arb)
    BASE_MAIS_PCT      : base + (VD - demanda_min) * pct_excedente (CAMARB)
    FAIXA_FIXA         : valor_fixo tabelado por faixa (CEMAPE med admin)
    HORA_TRABALHADA    : valor_hora por faixa, min de horas, regra de fração (CEMAPE med honor.)
    """
    PERCENTUAL_DEMANDA = 'PERCENTUAL_DEMANDA', 'Percentual da Demanda (com piso/teto)'
    FIXO = 'FIXO', 'Valor Fixo Único'
    INTERPOLACAO = 'INTERPOLACAO', 'Interpolação Linear por Faixa'
    BASE_MAIS_PCT = 'BASE_MAIS_PCT', 'Base + % sobre Excedente da Faixa'
    FAIXA_FIXA = 'FAIXA_FIXA', 'Valor Fixo por Faixa'
    HORA_TRABALHADA = 'HORA_TRABALHADA', 'Por Hora Trabalhada'


# ---------------------------------------------------------------------------
# TabelaCustas — define UM tipo de taxa para UMA combinação instituição/procedimento
# ---------------------------------------------------------------------------

class TabelaCustas(BaseModel):
    """
    Agrupa as faixas de uma taxa específica.
    Ex: 'CEMAPE / ARBITRAGEM / HONORARIOS / INTERPOLACAO'
    """
    instituicao = models.CharField(max_length=10, choices=Instituicao.choices, verbose_name='Instituição')
    tipo_procedimento = models.CharField(max_length=15, choices=TipoProcedimento.choices, verbose_name='Tipo de Procedimento')
    tipo_taxa = models.CharField(max_length=15, choices=TipoTaxa.choices, verbose_name='Tipo de Taxa')
    metodo_calculo = models.CharField(max_length=20, choices=MetodoCalculo.choices, verbose_name='Método de Cálculo')
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    ativa = models.BooleanField(default=True)
    vigente_a_partir = models.DateField(verbose_name='Vigente a partir de')

    class Meta:
        verbose_name = 'Tabela de Custas'
        verbose_name_plural = 'Tabelas de Custas'
        ordering = ['instituicao', 'tipo_procedimento', 'tipo_taxa']
        unique_together = [('instituicao', 'tipo_procedimento', 'tipo_taxa', 'vigente_a_partir')]

    def __str__(self):
        return f'{self.instituicao} | {self.get_tipo_procedimento_display()} | {self.get_tipo_taxa_display()}'


# ---------------------------------------------------------------------------
# FaixaCustas — uma linha da tabela, define o range de VD e os valores
# ---------------------------------------------------------------------------

class FaixaCustas(BaseModel):
    """
    Uma faixa do Valor da Demanda com os parâmetros de cálculo correspondentes.
    Os campos utilizados dependem do MetodoCalculo da TabelaCustas pai.

    INTERPOLACAO:   usa demanda_min, demanda_max, valor_min, valor_max
    BASE_MAIS_PCT:  usa demanda_min, demanda_max, valor_base, pct_excedente, (valor_teto)
    FAIXA_FIXA:     usa demanda_min, demanda_max, valor_fixo
    HORA_TRABALHADA:usa demanda_min, demanda_max, valor_fixo (= valor da hora)
    """
    tabela = models.ForeignKey(TabelaCustas, on_delete=models.CASCADE, related_name='faixas')
    ordem = models.PositiveSmallIntegerField(help_text='Ordem de exibição/avaliação')

    demanda_min = models.DecimalField(max_digits=18, decimal_places=2, verbose_name='VD mínimo (R$)')
    demanda_max = models.DecimalField(
        max_digits=18, decimal_places=2,
        null=True, blank=True,
        verbose_name='VD máximo (R$)',
        help_text='Deixar em branco para faixa aberta (último escalão)',
    )

    # INTERPOLACAO
    valor_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Valor mín da taxa (R$)')
    valor_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Valor máx da taxa (R$)')

    # BASE_MAIS_PCT
    valor_base = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Valor base (R$)')
    pct_excedente = models.DecimalField(
        max_digits=8, decimal_places=4,
        null=True, blank=True,
        verbose_name='% sobre excedente',
        help_text='Ex: 1.98 para 1,980%',
    )

    # FAIXA_FIXA e HORA_TRABALHADA
    valor_fixo = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        verbose_name='Valor fixo / Valor hora (R$)',
    )

    # Teto para BASE_MAIS_PCT (ex: max R$360.000 CAMARB admin)
    valor_teto_faixa = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        verbose_name='Teto desta faixa (R$)',
    )

    class Meta:
        verbose_name = 'Faixa de Custas'
        verbose_name_plural = 'Faixas de Custas'
        ordering = ['tabela', 'ordem']

    def __str__(self):
        teto = f'até {self.demanda_max:,.0f}' if self.demanda_max else 'acima'
        return f'Faixa {self.ordem}: {self.demanda_min:,.0f} — {teto}'


# ---------------------------------------------------------------------------
# ConfiguracaoCalculadora — parâmetros escalares (%, pisos, tetos, modificadores)
# ---------------------------------------------------------------------------

class ConfiguracaoCalculadora(BaseModel):
    """
    Armazena todos os escalares editáveis:
      - percentuais de registro, pisos e tetos
      - modificadores de honorários (árbitro único, presidente, expedita)
      - mínimos de horas (mediação)
      - tetos globais de honorários (CAMARB)

    Chaves conhecidas:
      CEMAPE/ARBITRAGEM: taxa_registro_pct, taxa_registro_piso, taxa_registro_teto,
                         arbitro_unico_adicional_pct, tribunal_presidente_adicional_pct,
                         expedita_desconto_pct
      CEMAPE/MEDIACAO:   taxa_registro_pct, taxa_registro_piso, taxa_registro_teto,
                         mediacao_horas_minimas
      CAMARB/ARBITRAGEM: taxa_registro_fixo,
                         arbitro_unico_adicional_pct, tribunal_presidente_adicional_pct,
                         co_arbitro_teto, presidente_teto, taxa_admin_teto
    """
    instituicao = models.CharField(max_length=10, choices=Instituicao.choices, verbose_name='Instituição')
    tipo_procedimento = models.CharField(max_length=15, choices=TipoProcedimento.choices, verbose_name='Procedimento')
    chave = models.CharField(max_length=60, verbose_name='Chave')
    valor = models.DecimalField(max_digits=18, decimal_places=6, verbose_name='Valor')
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Configuração da Calculadora'
        verbose_name_plural = 'Configurações da Calculadora'
        ordering = ['instituicao', 'tipo_procedimento', 'chave']
        unique_together = [('instituicao', 'tipo_procedimento', 'chave')]

    def __str__(self):
        return f'{self.instituicao}/{self.tipo_procedimento} · {self.chave} = {self.valor}'
