from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("ncjm_site.site_urls")),
]

if settings.NCJM_API_ENABLED:
    urlpatterns += [
        path("api/", include("api.api_urls")),
        path("oauth2/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    ]

urlpatterns += static(
    settings.STATIC_URL,
    document_root=settings.STATIC_ROOT
)