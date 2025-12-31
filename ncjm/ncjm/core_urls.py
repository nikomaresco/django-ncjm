from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

urlpatterns = [
    path("ncjm-admin/", admin.site.urls),
    path("", include("ncjm_site.site_urls")),
]

if settings.NCJM_API_ENABLED:
    urlpatterns += [
        path("api/", include("api.api_urls")),
        path("oauth2/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    ]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
    urlpatterns += staticfiles_urlpatterns()
else:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )