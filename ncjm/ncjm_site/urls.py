from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("add-a-joke/", views.add_joke, name="add_joke"),
    path("<int:joke_id>/", views.index, name="joke_by_id"),
    path("<slug:joke_slug>/", views.index, name="joke_by_slug"),
]
