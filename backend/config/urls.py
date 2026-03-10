from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # Auth views (login/logout com Django sessions)
    path('auth/', include('apps.accounts.urls')),

    # Portal do cliente e painel interno (templates)
    path('', include('apps.tickets.urls')),
    path('knowledge/', include('apps.knowledge_base.urls')),

    # REST API
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
