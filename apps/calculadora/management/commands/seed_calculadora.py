"""
Management command: python manage.py seed_calculadora

Popula TabelaCustas, FaixaCustas e ConfiguracaoCalculadora com os valores
oficiais do CEMAPE (2024).

Pode ser re-executado com segurança (idempotente via get_or_create).
"""
from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.calculadora.models import (
    TabelaCustas, FaixaCustas, ConfiguracaoCalculadora,
    TipoProcedimento, TipoTaxa, MetodoCalculo,
)

VIGENCIA = date(2024, 1, 1)


class Command(BaseCommand):
    help = 'Seed das tabelas de custas do CEMAPE'

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_cemape_arbitragem()
        self._seed_cemape_mediacao()
        self.stdout.write(self.style.SUCCESS('Seed concluído com sucesso.'))

    # -----------------------------------------------------------------------
    # Utilitários
    # -----------------------------------------------------------------------

    def _tabela(self, inst, proc, tipo, metodo, descricao):
        obj, created = TabelaCustas.objects.get_or_create(
            instituicao=inst,
            tipo_procedimento=proc,
            tipo_taxa=tipo,
            vigente_a_partir=VIGENCIA,
            defaults={'metodo_calculo': metodo, 'descricao': descricao, 'ativa': True},
        )
        if created:
            self.stdout.write(f'  + Tabela criada: {obj}')
        else:
            # Garante que faixas existentes sejam recriadas apenas se não houver nenhuma
            self.stdout.write(f'  ~ Tabela já existia: {obj}')
        return obj

    def _faixas(self, tabela, faixas_data):
        """Cria as faixas somente se a tabela ainda não tiver nenhuma."""
        if tabela.faixas.exists():
            return
        for i, kwargs in enumerate(faixas_data, start=1):
            FaixaCustas.objects.create(tabela=tabela, ordem=i, **kwargs)

    def _cfg(self, inst, proc, chave, valor, descricao):
        obj, created = ConfiguracaoCalculadora.objects.get_or_create(
            instituicao=inst,
            tipo_procedimento=proc,
            chave=chave,
            defaults={'valor': valor, 'descricao': descricao, 'ativa': True},
        )
        if not created:
            obj.valor = valor
            obj.save(update_fields=['valor'])

    # -----------------------------------------------------------------------
    # CEMAPE — Arbitragem
    # -----------------------------------------------------------------------

    def _seed_cemape_arbitragem(self):
        self.stdout.write('CEMAPE Arbitragem')
        inst, proc = 'CEMAPE', TipoProcedimento.ARBITRAGEM

        # Configurações escalares
        cfgs = [
            ('taxa_registro_pct',                  Decimal('1'),    'Taxa de registro: 1% do VD'),
            ('taxa_registro_piso',                 Decimal('500'),  'Piso da taxa de registro'),
            ('taxa_registro_teto',                 Decimal('20000'),'Teto da taxa de registro'),
            ('arbitro_unico_adicional_pct',        Decimal('20'),   'Árbitro único: +20% sobre o valor base'),
            ('tribunal_presidente_adicional_pct',  Decimal('10'),   'Presidente do tribunal: +10% sobre a base'),
            ('expedita_desconto_pct',              Decimal('20'),   'Procedimento expedito: -20% sobre o valor base'),
        ]
        for chave, valor, desc in cfgs:
            self._cfg(inst, proc, chave, valor, desc)

        # Tabela de Administração (Interpolação)
        tab_admin = self._tabela(
            inst, proc, TipoTaxa.ADMINISTRACAO,
            MetodoCalculo.INTERPOLACAO,
            'Taxa de Administração CEMAPE Arbitragem (interpolação linear)',
        )
        self._faixas(tab_admin, [
            # demanda_min,  demanda_max,   valor_min, valor_max
            {'demanda_min': Decimal('0'),           'demanda_max': Decimal('50000'),      'valor_min': Decimal('1500'),    'valor_max': Decimal('1500')},
            {'demanda_min': Decimal('50000'),       'demanda_max': Decimal('100000'),     'valor_min': Decimal('1500'),    'valor_max': Decimal('3000')},
            {'demanda_min': Decimal('100000'),      'demanda_max': Decimal('200000'),     'valor_min': Decimal('3000'),    'valor_max': Decimal('5200')},
            {'demanda_min': Decimal('200000'),      'demanda_max': Decimal('300000'),     'valor_min': Decimal('5200'),    'valor_max': Decimal('6100')},
            {'demanda_min': Decimal('300000'),      'demanda_max': Decimal('500000'),     'valor_min': Decimal('6100'),    'valor_max': Decimal('6600')},
            {'demanda_min': Decimal('500000'),      'demanda_max': Decimal('750000'),     'valor_min': Decimal('6600'),    'valor_max': Decimal('7930')},
            {'demanda_min': Decimal('750000'),      'demanda_max': Decimal('1000000'),    'valor_min': Decimal('8930'),    'valor_max': Decimal('10400')},
            {'demanda_min': Decimal('1000000'),     'demanda_max': Decimal('2000000'),    'valor_min': Decimal('10400'),   'valor_max': Decimal('14810')},
            {'demanda_min': Decimal('2000000'),     'demanda_max': Decimal('5000000'),    'valor_min': Decimal('14810'),   'valor_max': Decimal('25600')},
            {'demanda_min': Decimal('5000000'),     'demanda_max': Decimal('10000000'),   'valor_min': Decimal('25600'),   'valor_max': Decimal('35120')},
            {'demanda_min': Decimal('10000000'),    'demanda_max': Decimal('20000000'),   'valor_min': Decimal('35120'),   'valor_max': Decimal('56050')},
            {'demanda_min': Decimal('20000000'),    'demanda_max': Decimal('40000000'),   'valor_min': Decimal('56050'),   'valor_max': Decimal('84390')},
            {'demanda_min': Decimal('40000000'),    'demanda_max': Decimal('80000000'),   'valor_min': Decimal('80440'),   'valor_max': Decimal('111750')},
            {'demanda_min': Decimal('80000000'),    'demanda_max': Decimal('150000000'),  'valor_min': Decimal('96090'),   'valor_max': Decimal('123130')},
            {'demanda_min': Decimal('150000000'),   'demanda_max': Decimal('250000000'),  'valor_min': Decimal('123130'),  'valor_max': Decimal('146110')},
            {'demanda_min': Decimal('250000000'),   'demanda_max': Decimal('500000000'),  'valor_min': Decimal('146110'),  'valor_max': Decimal('200000')},
        ])

        # Tabela de Honorários (Interpolação)
        tab_hon = self._tabela(
            inst, proc, TipoTaxa.HONORARIOS,
            MetodoCalculo.INTERPOLACAO,
            'Honorários base por árbitro CEMAPE Arbitragem (interpolação linear)',
        )
        self._faixas(tab_hon, [
            {'demanda_min': Decimal('0'),           'demanda_max': Decimal('50000'),      'valor_min': Decimal('3000'),    'valor_max': Decimal('3000')},
            {'demanda_min': Decimal('50000'),       'demanda_max': Decimal('100000'),     'valor_min': Decimal('3000'),    'valor_max': Decimal('6000')},
            {'demanda_min': Decimal('100000'),      'demanda_max': Decimal('200000'),     'valor_min': Decimal('6000'),    'valor_max': Decimal('11000')},
            {'demanda_min': Decimal('200000'),      'demanda_max': Decimal('300000'),     'valor_min': Decimal('11000'),   'valor_max': Decimal('13500')},
            {'demanda_min': Decimal('300000'),      'demanda_max': Decimal('500000'),     'valor_min': Decimal('13500'),   'valor_max': Decimal('16070')},
            {'demanda_min': Decimal('500000'),      'demanda_max': Decimal('750000'),     'valor_min': Decimal('16070'),   'valor_max': Decimal('20790')},
            {'demanda_min': Decimal('750000'),      'demanda_max': Decimal('1000000'),    'valor_min': Decimal('22920'),   'valor_max': Decimal('26070')},
            {'demanda_min': Decimal('1000000'),     'demanda_max': Decimal('2000000'),    'valor_min': Decimal('26070'),   'valor_max': Decimal('34560')},
            {'demanda_min': Decimal('2000000'),     'demanda_max': Decimal('5000000'),    'valor_min': Decimal('34560'),   'valor_max': Decimal('54580')},
            {'demanda_min': Decimal('5000000'),     'demanda_max': Decimal('10000000'),   'valor_min': Decimal('54580'),   'valor_max': Decimal('71120')},
            {'demanda_min': Decimal('10000000'),    'demanda_max': Decimal('20000000'),   'valor_min': Decimal('71120'),   'valor_max': Decimal('111910')},
            {'demanda_min': Decimal('20000000'),    'demanda_max': Decimal('40000000'),   'valor_min': Decimal('111910'),  'valor_max': Decimal('163170')},
            {'demanda_min': Decimal('40000000'),    'demanda_max': Decimal('80000000'),   'valor_min': Decimal('155010'),  'valor_max': Decimal('212620')},
            {'demanda_min': Decimal('80000000'),    'demanda_max': Decimal('150000000'),  'valor_min': Decimal('192850'),  'valor_max': Decimal('251750')},
            {'demanda_min': Decimal('150000000'),   'demanda_max': Decimal('250000000'),  'valor_min': Decimal('251750'),  'valor_max': Decimal('296400')},
            {'demanda_min': Decimal('250000000'),   'demanda_max': Decimal('500000000'),  'valor_min': Decimal('296400'),  'valor_max': Decimal('350000')},
        ])

    # -----------------------------------------------------------------------
    # CEMAPE — Mediação
    # -----------------------------------------------------------------------

    def _seed_cemape_mediacao(self):
        self.stdout.write('CEMAPE Mediação')
        inst, proc = 'CEMAPE', TipoProcedimento.MEDIACAO

        cfgs = [
            ('taxa_registro_pct',    Decimal('0.5'),  'Taxa de registro: 0,5% do VD'),
            ('taxa_registro_piso',   Decimal('100'),  'Piso da taxa de registro mediação'),
            ('taxa_registro_teto',   Decimal('5000'), 'Teto da taxa de registro mediação'),
            ('mediacao_horas_minimas', Decimal('3'),  'Mínimo de horas faturadas na mediação'),
        ]
        for chave, valor, desc in cfgs:
            self._cfg(inst, proc, chave, valor, desc)

        # Taxa de Administração (valor fixo por faixa)
        tab_admin = self._tabela(
            inst, proc, TipoTaxa.ADMINISTRACAO,
            MetodoCalculo.FAIXA_FIXA,
            'Taxa de Administração CEMAPE Mediação (fixo por faixa)',
        )
        self._faixas(tab_admin, [
            {'demanda_min': Decimal('0'),          'demanda_max': Decimal('10000'),       'valor_fixo': Decimal('300')},
            {'demanda_min': Decimal('10000'),       'demanda_max': Decimal('25000'),       'valor_fixo': Decimal('500')},
            {'demanda_min': Decimal('25000'),       'demanda_max': Decimal('50000'),       'valor_fixo': Decimal('800')},
            {'demanda_min': Decimal('50000'),       'demanda_max': Decimal('100000'),      'valor_fixo': Decimal('1200')},
            {'demanda_min': Decimal('100000'),      'demanda_max': Decimal('250000'),      'valor_fixo': Decimal('2000')},
            {'demanda_min': Decimal('250000'),      'demanda_max': Decimal('500000'),      'valor_fixo': Decimal('3000')},
            {'demanda_min': Decimal('500000'),      'demanda_max': Decimal('1000000'),     'valor_fixo': Decimal('4500')},
            {'demanda_min': Decimal('1000000'),     'demanda_max': Decimal('2500000'),     'valor_fixo': Decimal('6500')},
            {'demanda_min': Decimal('2500000'),     'demanda_max': Decimal('5000000'),     'valor_fixo': Decimal('9000')},
            {'demanda_min': Decimal('5000000'),     'demanda_max': Decimal('10000000'),    'valor_fixo': Decimal('13000')},
            {'demanda_min': Decimal('10000000'),    'demanda_max': Decimal('25000000'),    'valor_fixo': Decimal('18000')},
            {'demanda_min': Decimal('25000000'),    'demanda_max': Decimal('50000000'),    'valor_fixo': Decimal('22000')},
            {'demanda_min': Decimal('50000000'),    'demanda_max': Decimal('100000000'),   'valor_fixo': Decimal('26000')},
            {'demanda_min': Decimal('100000000'),   'demanda_max': None,                   'valor_fixo': Decimal('30000')},
        ])

        # Honorários (por hora, fixo por faixa)
        tab_hon = self._tabela(
            inst, proc, TipoTaxa.HONORARIOS,
            MetodoCalculo.HORA_TRABALHADA,
            'Honorários do mediador CEMAPE (valor/hora por faixa)',
        )
        self._faixas(tab_hon, [
            {'demanda_min': Decimal('0'),          'demanda_max': Decimal('10000'),       'valor_fixo': Decimal('100')},
            {'demanda_min': Decimal('10000'),       'demanda_max': Decimal('25000'),       'valor_fixo': Decimal('150')},
            {'demanda_min': Decimal('25000'),       'demanda_max': Decimal('50000'),       'valor_fixo': Decimal('200')},
            {'demanda_min': Decimal('50000'),       'demanda_max': Decimal('100000'),      'valor_fixo': Decimal('300')},
            {'demanda_min': Decimal('100000'),      'demanda_max': Decimal('250000'),      'valor_fixo': Decimal('450')},
            {'demanda_min': Decimal('250000'),      'demanda_max': Decimal('500000'),      'valor_fixo': Decimal('650')},
            {'demanda_min': Decimal('500000'),      'demanda_max': Decimal('1000000'),     'valor_fixo': Decimal('900')},
            {'demanda_min': Decimal('1000000'),     'demanda_max': Decimal('2500000'),     'valor_fixo': Decimal('1200')},
            {'demanda_min': Decimal('2500000'),     'demanda_max': Decimal('5000000'),     'valor_fixo': Decimal('1500')},
            {'demanda_min': Decimal('5000000'),     'demanda_max': Decimal('10000000'),    'valor_fixo': Decimal('1900')},
            {'demanda_min': Decimal('10000000'),    'demanda_max': Decimal('25000000'),    'valor_fixo': Decimal('2300')},
            {'demanda_min': Decimal('25000000'),    'demanda_max': Decimal('50000000'),    'valor_fixo': Decimal('2600')},
            {'demanda_min': Decimal('50000000'),    'demanda_max': Decimal('100000000'),   'valor_fixo': Decimal('2800')},
            {'demanda_min': Decimal('100000000'),   'demanda_max': None,                   'valor_fixo': Decimal('3000')},
        ])

