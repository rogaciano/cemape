from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.core.forms import TailwindFormMixin
from .models import UserProfile


class LoginForm(TailwindFormMixin, AuthenticationForm):
    pass


class UserProfileForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['telefone', 'oab']


class CertificadoLoginForm(forms.Form):
    certificado = forms.FileField(
        label='Certificado Digital (.pfx / .p12)',
        help_text='Arquivo .pfx ou .p12 do seu e-CPF ICP-Brasil',
        widget=forms.FileInput(attrs={
            'accept': '.pfx,.p12',
            'class': (
                'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm '
                'file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 '
                'file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 '
                'hover:file:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500'
            ),
        }),
    )
    senha_certificado = forms.CharField(
        label='Senha do Certificado',
        widget=forms.PasswordInput(attrs={
            'class': (
                'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm '
                'focus:outline-none focus:ring-2 focus:ring-blue-500'
            ),
            'placeholder': 'Senha de proteção do arquivo .pfx',
        }),
    )
