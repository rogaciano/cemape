from django.contrib.auth import views as auth_views, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import LoginForm, UserProfileForm, CertificadoLoginForm
from .models import UserProfile
from .services.icp_brasil import validar_pfx


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


class LogoutView(auth_views.LogoutView):
    pass


def login_certificado(request):
    """Login via certificado digital e-CPF ICP-Brasil (.pfx / .p12)."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CertificadoLoginForm(request.POST, request.FILES)
        if form.is_valid():
            pfx_bytes = request.FILES['certificado'].read()
            senha = form.cleaned_data['senha_certificado']
            try:
                info = validar_pfx(pfx_bytes, senha)
                cpf = info['cpf']

                # Buscar perfil existente pelo CPF
                profile = UserProfile.objects.filter(cpf=cpf).select_related('user').first()

                if profile:
                    user = profile.user
                else:
                    # Criar novo usuário vinculado ao CPF
                    username = f'cpf_{cpf}'
                    user, created = User.objects.get_or_create(username=username)
                    if created:
                        nome_partes = info['nome'].split()
                        user.first_name = nome_partes[0] if nome_partes else ''
                        user.last_name = ' '.join(nome_partes[1:]) if len(nome_partes) > 1 else ''
                        user.set_unusable_password()
                        user.save()
                    profile = user.profile
                    profile.cpf = cpf

                # Atualizar dados do certificado no perfil
                profile.cert_nome = info['nome']
                profile.cert_emissor = info['emissor']
                profile.cert_valido_ate = info['valido_ate']
                profile.save()

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(
                    request,
                    f'Bem-vindo(a), {user.get_full_name() or info["nome"]}! '
                    f'Certificado validado com sucesso.'
                )
                return redirect(request.GET.get('next', 'dashboard'))

            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = CertificadoLoginForm()

    return render(request, 'accounts/login_certificado.html', {'form': form})


@login_required
def perfil(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('accounts:perfil')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'accounts/perfil.html', {'form': form})
