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
