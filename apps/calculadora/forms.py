from decimal import Decimal
from django import forms


class CalculadoraForm(forms.Form):
    PROCEDIMENTO_CHOICES = [
        ('ARBITRAGEM', 'Arbitragem'),
        ('MEDIACAO', 'Mediação'),
    ]
    ARBITROS_CHOICES = [
        (1, 'Árbitro Único'),
        (3, 'Tribunal (3 árbitros)'),
    ]

    valor_demanda = forms.DecimalField(
        label='Valor Econômico da Demanda (R$)',
        min_value=Decimal('1.00'),
        max_digits=18,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 text-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'placeholder': '0,00',
            'step': '0.01',
        }),
    )
    tipo_procedimento = forms.ChoiceField(
        label='Tipo de Procedimento',
        choices=PROCEDIMENTO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'mr-2'}),
    )
    quantidade_arbitros = forms.TypedChoiceField(
        label='Composição do Juízo',
        choices=ARBITROS_CHOICES,
        coerce=int,
        initial=1,
        widget=forms.RadioSelect(attrs={'class': 'mr-2'}),
    )
    procedimento_expedito = forms.BooleanField(
        label='Procedimento Expedito',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
    )
    horas_trabalhadas = forms.DecimalField(
        label='Horas trabalhadas por mediador',
        required=False,
        min_value=Decimal('0'),
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none',
            'placeholder': 'Ex: 4.5 para 4h30min',
            'step': '0.5',
        }),
        help_text='Frações de hora: até 30 min = meia hora; acima = hora cheia.',
    )
    quantidade_mediadores = forms.IntegerField(
        label='Quantidade de Mediadores',
        min_value=1,
        max_value=10,
        initial=1,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none',
            'min': '1',
            'max': '10',
        }),
        help_text='Informe quantos mediadores participam da sessão.',
    )
