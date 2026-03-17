from django import forms

from apps.core.forms import TailwindFormMixin
from .models import Processo, Andamento, Documento


class ProcessoForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Processo
        fields = [
            'demandado_nome', 'demandado_email',
            'tipo', 'descricao', 'valor_reclamado',
            'sede', 'confidencial',
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 5}),
        }


class AtribuirArbitroForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Processo
        fields = ['arbitro']


class AndamentoForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Andamento
        fields = ['descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }


class DocumentoForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['titulo', 'arquivo', 'descricao']
