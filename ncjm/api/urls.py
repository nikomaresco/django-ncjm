from django.urls import path

from api.joke.joke import (
    get_random_joke,
    get_joke_by_id,
    get_joke_by_slug,
    delete_joke,
    create_joke,
    update_joke,
)

urlpatterns = [
    path("joke/random/", get_random_joke),
    path("joke/<int:id>/", get_joke_by_id),
    path("joke/<slug:slug>/", get_joke_by_slug),
    path("joke/delete/<int:id>/", delete_joke),
    path("joke/create/", create_joke),
    path("joke/update/<int:id>/", update_joke),
]