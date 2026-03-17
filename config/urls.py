from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='dashboard'), name='home'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('processos/', include('apps.processos.urls', namespace='processos')),
    path('dashboard/', include('apps.core.urls')),
    path('calculadora/', include('apps.calculadora.urls', namespace='calculadora')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__reload__/', include('django_browser_reload.urls'))]
