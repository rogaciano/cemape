from django.contrib import admin
from .models import Processo, Documento, Andamento


class AndamentoInline(admin.TabularInline):
    model = Andamento
    extra = 0
    readonly_fields = ['registrado_por', 'created_at']


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0
    readonly_fields = ['enviado_por', 'created_at']


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'demandante', 'demandado_nome', 'status', 'arbitro', 'created_at']
    list_filter = ['status', 'tipo', 'confidencial']
    search_fields = ['numero', 'demandante__username', 'demandado_nome']
    inlines = [AndamentoInline, DocumentoInline]
    readonly_fields = ['numero', 'criado_por', 'created_at', 'updated_at']
