from django.db import transaction
from django.utils import timezone

from apps.processos.models import Processo, Andamento, StatusProcesso


class ProcessoService:

    @staticmethod
    def gerar_numero():
        ano = timezone.now().year
        ultimo = (
            Processo.objects.filter(numero__startswith=str(ano))
            .order_by('-numero')
            .first()
        )
        if ultimo:
            seq = int(ultimo.numero.split('/')[0][-4:]) + 1
        else:
            seq = 1
        return f'{ano}{seq:04d}/{ano}'

    @staticmethod
    @transaction.atomic
    def abrir_processo(demandante, dados, criado_por):
        numero = ProcessoService.gerar_numero()
        processo = Processo.objects.create(
            numero=numero,
            demandante=demandante,
            criado_por=criado_por,
            **dados,
        )
        Andamento.objects.create(
            processo=processo,
            descricao='Processo aberto. Aguardando resposta do demandado.',
            registrado_por=criado_por,
        )
        return processo

    @staticmethod
    @transaction.atomic
    def atribuir_arbitro(processo, arbitro, secretaria):
        if processo.status not in (StatusProcesso.AGUARDANDO, StatusProcesso.EM_ANDAMENTO):
            raise ValueError('Não é possível atribuir árbitro neste status.')
        processo.arbitro = arbitro
        processo.status = StatusProcesso.EM_ANDAMENTO
        processo.save()
        Andamento.objects.create(
            processo=processo,
            descricao=f'Árbitro {arbitro.get_full_name()} atribuído ao processo.',
            registrado_por=secretaria,
        )
        return processo

    @staticmethod
    @transaction.atomic
    def encerrar_processo(processo, descricao_sentenca, secretaria):
        if processo.status == StatusProcesso.ENCERRADO:
            raise ValueError('Processo já encerrado.')
        processo.status = StatusProcesso.ENCERRADO
        processo.save()
        Andamento.objects.create(
            processo=processo,
            descricao=f'Processo encerrado. {descricao_sentenca}',
            registrado_por=secretaria,
        )
        return processo
