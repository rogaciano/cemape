from django.urls import path
from . import views

app_name = 'processos'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('novo/', views.novo, name='novo'),
    path('<uuid:pk>/', views.detalhe, name='detalhe'),
    path('<uuid:pk>/arbitro/', views.atribuir_arbitro, name='atribuir_arbitro'),
    path('<uuid:pk>/andamento/', views.registrar_andamento, name='registrar_andamento'),
    path('<uuid:pk>/encerrar/', views.encerrar, name='encerrar'),
]
