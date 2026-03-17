from django.db import models


class ProcessoQuerySet(models.QuerySet):
    def aguardando(self):
        return self.filter(status='AGUARDANDO')

    def em_andamento(self):
        return self.filter(status='EM_ANDAMENTO')

    def do_demandante(self, user):
        return self.filter(demandante=user)

    def do_arbitro(self, user):
        return self.filter(arbitro=user)

    def publicos(self):
        return self.filter(confidencial=False)

    def com_relacionados(self):
        return self.select_related('demandante', 'arbitro', 'criado_por')


class ProcessoManager(models.Manager):
    def get_queryset(self):
        return ProcessoQuerySet(self.model, using=self._db)

    def aguardando(self):
        return self.get_queryset().aguardando()

    def em_andamento(self):
        return self.get_queryset().em_andamento()

    def do_demandante(self, user):
        return self.get_queryset().do_demandante(user)

    def do_arbitro(self, user):
        return self.get_queryset().do_arbitro(user)

    def publicos(self):
        return self.get_queryset().publicos()

    def com_relacionados(self):
        return self.get_queryset().com_relacionados()
