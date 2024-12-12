from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("api.api_urls")),

    path("oauth2/", include("oauth2_provider.urls", namespace="oauth2_provider")),

    path("", include("ncjm_site.site_urls")),
]
