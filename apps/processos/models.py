from django.contrib.auth.models import User
from django.db import models

from apps.core.models import BaseModel
from .managers import ProcessoManager


class StatusProcesso(models.TextChoices):
    AGUARDANDO = 'AGUARDANDO', 'Aguardando Resposta'
    EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
    SUSPENSO = 'SUSPENSO', 'Suspenso'
    ENCERRADO = 'ENCERRADO', 'Encerrado'
    EXTINTO = 'EXTINTO', 'Extinto'


class TipoArbitragem(models.TextChoices):
    DIREITO = 'DIREITO', 'Por Direito'
    EQUIDADE = 'EQUIDADE', 'Por Equidade'


class Processo(BaseModel):
    numero = models.CharField(max_length=20, unique=True, verbose_name='Número')
    status = models.CharField(
        max_length=20,
        choices=StatusProcesso.choices,
        default=StatusProcesso.AGUARDANDO,
    )
    tipo = models.CharField(
        max_length=10,
        choices=TipoArbitragem.choices,
        default=TipoArbitragem.DIREITO,
    )

    # Partes
    demandante = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='processos_como_demandante',
        verbose_name='Demandante',
    )
    demandado_nome = models.CharField(max_length=200, verbose_name='Nome do Demandado')
    demandado_email = models.EmailField(blank=True, verbose_name='E-mail do Demandado')

    # Mérito
    descricao = models.TextField(verbose_name='Descrição do Litígio')
    valor_reclamado = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        verbose_name='Valor Reclamado (R$)',
    )

    # Árbitro
    arbitro = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processos_como_arbitro',
        verbose_name='Árbitro',
        limit_choices_to={'profile__role': 'ARBITRO'},
    )

    sede = models.CharField(max_length=100, blank=True, verbose_name='Sede da Arbitragem')
    confidencial = models.BooleanField(default=True, verbose_name='Processo Confidencial')
    criado_por = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='processos_criados',
        verbose_name='Criado por',
    )

    class Meta:
        verbose_name = 'Processo Arbitral'
        verbose_name_plural = 'Processos Arbitrais'
        ordering = ['-created_at']
        permissions = [
            ('pode_atribuir_arbitro', 'Pode atribuir árbitro ao processo'),
            ('pode_encerrar_processo', 'Pode encerrar processo'),
            ('pode_ver_confidencial', 'Pode ver processos confidenciais'),
        ]

    objects = ProcessoManager()

    def __str__(self):
        return f'Processo {self.numero}'


class Documento(BaseModel):
    processo = models.ForeignKey(
        Processo, on_delete=models.CASCADE,
        related_name='documentos',
    )
    titulo = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='processos/documentos/%Y/%m/')
    enviado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo


class Andamento(BaseModel):
    processo = models.ForeignKey(
        Processo, on_delete=models.CASCADE,
        related_name='andamentos',
    )
    descricao = models.TextField(verbose_name='Descrição do Andamento')
    registrado_por = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Andamento'
        verbose_name_plural = 'Andamentos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Andamento em {self.processo.numero} — {self.created_at:%d/%m/%Y}'
