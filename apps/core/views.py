from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.processos.models import Processo


@login_required
def dashboard(request):
    user = request.user
    processos_qs = Processo.objects.all()

    if hasattr(user, 'profile') and user.profile.is_secretaria_ou_acima():
        total = processos_qs.count()
        aguardando = processos_qs.filter(status='AGUARDANDO').count()
        em_andamento = processos_qs.filter(status='EM_ANDAMENTO').count()
        encerrados = processos_qs.filter(status='ENCERRADO').count()
        recentes = processos_qs.order_by('-created_at')[:5]
    else:
        total = aguardando = em_andamento = encerrados = 0
        recentes = Processo.objects.none()

    return render(request, 'dashboard.html', {
        'total': total,
        'aguardando': aguardando,
        'em_andamento': em_andamento,
        'encerrados': encerrados,
        'recentes': recentes,
    })
