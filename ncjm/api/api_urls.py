from django.urls import path

from api.endpoints.joke import JokeListCreateView, JokeRetrieveUpdateDestroyView, RandomJokeView
from api.endpoints.reaction import AllowedReactionsView, JokeReactionCreateView
from api.endpoints.submitter import SubmitterJokesListView, SubmitterListView
from api.endpoints.tag import TagJokesListView, TagListCreateView, TagRetrieveUpdateDestroyView

urlpatterns = [
    path("v1/reactions/options/", AllowedReactionsView.as_view(), name="reactions-options"),

    path("v1/jokes/", JokeListCreateView.as_view(), name="jokes-list-create"),
    path("v1/jokes/random/", RandomJokeView.as_view(), name="jokes-random"),
    path("v1/jokes/<int:pk>/", JokeRetrieveUpdateDestroyView.as_view(), name="jokes-detail"),
    path("v1/jokes/<int:pk>/reactions/", JokeReactionCreateView.as_view(), name="jokes-reactions-create"),

    path("v1/tags/", TagListCreateView.as_view(), name="tags-list-create"),
    path("v1/tags/<int:pk>/", TagRetrieveUpdateDestroyView.as_view(), name="tags-detail"),
    path("v1/tags/<str:tag_text>/jokes/", TagJokesListView.as_view(), name="tags-jokes"),

    path("v1/submitters/", SubmitterListView.as_view(), name="submitters-list"),
    path("v1/submitters/<str:submitter_name>/jokes/", SubmitterJokesListView.as_view(), name="submitter-jokes"),
]