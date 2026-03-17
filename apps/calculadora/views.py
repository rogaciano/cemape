"""
Views da Calculadora — TOTALMENTE PÚBLICAS (sem autenticação).
"""
from decimal import Decimal

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import CalculadoraForm
from .services.calculadora_service import CalculadoraService, EntradaCalculadora


def calculadora(request):
    """Página principal da calculadora (GET)."""
    form = CalculadoraForm()
    return render(request, 'calculadora/calculadora.html', {'form': form})


@require_http_methods(['POST'])
def calcular(request):
    """
    Endpoint HTMX: recebe POST, executa o cálculo e retorna o partial de resultado.
    Não exige autenticação — não usa @login_required nem qualquer middleware de sessão.
    """
    form = CalculadoraForm(request.POST)
    resultado = None
    erro = None

    if form.is_valid():
        dados = form.cleaned_data
        entrada = EntradaCalculadora(
            valor_demanda=dados['valor_demanda'],
            tipo_procedimento=dados['tipo_procedimento'],
            quantidade_arbitros=dados['quantidade_arbitros'],
            procedimento_expedito=dados.get('procedimento_expedito', False),
            horas_trabalhadas=dados.get('horas_trabalhadas') or None,
        )
        try:
            service = CalculadoraService()
            resultado = service.calcular(entrada)
        except Exception as exc:
            erro = str(exc)

    return render(request, 'calculadora/resultado_partial.html', {
        'form': form,
        'resultado': resultado,
        'erro': erro,
        'entrada': form.cleaned_data if form.is_valid() else None,
    })
