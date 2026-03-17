from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import LoginForm, UserProfileForm


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


class LogoutView(auth_views.LogoutView):
    pass


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
