from django.contrib import admin
from django.urls import path, include

from . import site_views

urlpatterns = [
    path("", site_views.index, name="index"),
    path("search/", site_views.search, name="search"),
    path("add-a-joke/", site_views.add_joke, name="add_joke"),
    path("<int:joke_id>/", site_views.index, name="joke_by_id"),
    path("<slug:joke_slug>/", site_views.index, name="joke_by_slug"),
]