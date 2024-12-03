from django.urls import path

from api.endpoints.joke import create_read_joke, update_delete_joke
from api.endpoints.tag import create_tag, get_or_delete_tag
from api.endpoints.submitter import get_jokes_by_submitter

urlpatterns = [
    # joke endpoint
    path("joke/", create_read_joke),
    path("joke/<int:id>/", update_delete_joke),

    # tag endpoint
    path("tag/", create_tag),
    path("tag/<str:tag_text>/", get_or_delete_tag),

    # submitter endpoint
    path("submitter/<str:submitter_name>", get_jokes_by_submitter),
]