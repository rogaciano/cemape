from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import BaseModel


class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrador'
    SECRETARIA = 'SECRETARIA', 'Secretaria'
    ARBITRO = 'ARBITRO', 'Árbitro'
    PARTE = 'PARTE', 'Parte / Representante'


class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTE)
    telefone = models.CharField(max_length=20, blank=True)
    oab = models.CharField(max_length=30, blank=True, verbose_name='OAB')
    cpf = models.CharField(max_length=11, blank=True, unique=True, null=True,
                           verbose_name='CPF', help_text='Somente números, 11 dígitos')
    cert_nome = models.CharField(max_length=255, blank=True,
                                 verbose_name='Nome no Certificado')
    cert_emissor = models.CharField(max_length=255, blank=True,
                                    verbose_name='Emissor do Certificado')
    cert_valido_ate = models.DateTimeField(null=True, blank=True,
                                           verbose_name='Certificado válido até')

    def is_admin(self):
        return self.role == Role.ADMIN

    def is_secretaria_ou_acima(self):
        return self.role in (Role.ADMIN, Role.SECRETARIA)

    def is_arbitro(self):
        return self.role == Role.ARBITRO

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
