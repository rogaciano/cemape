from django.urls import path
from . import views

app_name = 'calculadora'

urlpatterns = [
    path('', views.calculadora, name='index'),
    path('calcular/', views.calcular, name='calcular'),
]
