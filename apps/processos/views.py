from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AtribuirArbitroForm, AndamentoForm, DocumentoForm, ProcessoForm
from .models import Processo
from .services.processo_service import ProcessoService


@login_required
def lista(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if profile and profile.is_secretaria_ou_acima():
        qs = Processo.objects.all()
    elif profile and profile.is_arbitro():
        qs = Processo.objects.do_arbitro(user)
    else:
        qs = Processo.objects.do_demandante(user)

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    qs = qs.com_relacionados()
    return render(request, 'processos/lista.html', {'processos': qs})


@login_required
def detalhe(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    andamentos = processo.andamentos.select_related('registrado_por').order_by('-created_at')
    documentos = processo.documentos.select_related('enviado_por').order_by('-created_at')
    arbitros_disponiveis = User.objects.filter(profile__role='ARBITRO').select_related('profile')
    andamento_form = AndamentoForm()
    documento_form = DocumentoForm()
    return render(request, 'processos/detalhe.html', {
        'processo': processo,
        'andamentos': andamentos,
        'documentos': documentos,
        'arbitros_disponiveis': arbitros_disponiveis,
        'andamento_form': andamento_form,
        'documento_form': documento_form,
    })


@login_required
def novo(request):
    if request.method == 'POST':
        form = ProcessoForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            try:
                processo = ProcessoService.abrir_processo(
                    demandante=request.user,
                    dados=dados,
                    criado_por=request.user,
                )
                messages.success(request, f'Processo {processo.numero} aberto com sucesso.')
                return redirect('processos:detalhe', pk=processo.pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = ProcessoForm()
    return render(request, 'processos/form.html', {'form': form, 'titulo': 'Novo Processo'})


@permission_required('processos.pode_atribuir_arbitro', raise_exception=True)
def atribuir_arbitro(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == 'POST':
        form = AtribuirArbitroForm(request.POST, instance=processo)
        if form.is_valid():
            arbitro = form.cleaned_data['arbitro']
            try:
                ProcessoService.atribuir_arbitro(processo, arbitro, request.user)
                messages.success(request, 'Árbitro atribuído.')
            except ValueError as e:
                messages.error(request, str(e))
        if request.htmx:
            return render(request, 'processos/components/arbitro_partial.html', {'processo': processo})
    return redirect('processos:detalhe', pk=pk)


@login_required
def registrar_andamento(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == 'POST':
        form = AndamentoForm(request.POST)
        if form.is_valid():
            andamento = form.save(commit=False)
            andamento.processo = processo
            andamento.registrado_por = request.user
            andamento.save()
            messages.success(request, 'Andamento registrado.')
        if request.htmx:
            andamentos = processo.andamentos.select_related('registrado_por').order_by('-created_at')
            return render(request, 'processos/components/andamentos_partial.html', {
                'andamentos': andamentos,
                'andamento_form': AndamentoForm(),
            })
    return redirect('processos:detalhe', pk=pk)


@permission_required('processos.pode_encerrar_processo', raise_exception=True)
def encerrar(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == 'POST':
        descricao = request.POST.get('descricao_sentenca', '').strip()
        try:
            ProcessoService.encerrar_processo(processo, descricao, request.user)
            messages.success(request, 'Processo encerrado.')
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('processos:detalhe', pk=pk)
