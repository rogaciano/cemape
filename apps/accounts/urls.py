from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/certificado/', views.login_certificado, name='login_certificado'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
]
