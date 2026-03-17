from django.contrib import admin
from .models import TabelaCustas, FaixaCustas, ConfiguracaoCalculadora


class FaixaCustasInline(admin.TabularInline):
    model = FaixaCustas
    extra = 1
    ordering = ['ordem']
    fields = [
        'ordem', 'demanda_min', 'demanda_max',
        'valor_min', 'valor_max',          # INTERPOLACAO
        'valor_base', 'pct_excedente',     # BASE_MAIS_PCT
        'valor_fixo',                       # FAIXA_FIXA / HORA_TRABALHADA
        'valor_teto_faixa',
    ]


@admin.register(TabelaCustas)
class TabelaCustasAdmin(admin.ModelAdmin):
    list_display = [
        'instituicao', 'tipo_procedimento', 'tipo_taxa',
        'metodo_calculo', 'vigente_a_partir', 'ativa',
    ]
    list_filter = ['instituicao', 'tipo_procedimento', 'tipo_taxa', 'ativa']
    inlines = [FaixaCustasInline]
    save_on_top = True


@admin.register(ConfiguracaoCalculadora)
class ConfiguracaoCalculadoraAdmin(admin.ModelAdmin):
    list_display = ['instituicao', 'tipo_procedimento', 'chave', 'valor', 'descricao', 'ativa']
    list_filter = ['instituicao', 'tipo_procedimento', 'ativa']
    list_editable = ['valor', 'ativa']
    search_fields = ['chave', 'descricao']
    ordering = ['instituicao', 'tipo_procedimento', 'chave']
