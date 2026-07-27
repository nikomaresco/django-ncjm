from django.db.models import Count

from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from ncjm.models import Joke
from ..serializers import JokeReadSerializer, SubmitterSerializer


def _visible_jokes_for_request(request):
    queryset = Joke.objects.filter(is_deleted=False).prefetch_related("tags")

    if request.user.is_authenticated and request.user.is_staff:
        return queryset

    return queryset.filter(is_approved=True)


class SubmitterListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SubmitterSerializer

    def get_queryset(self):
        return (
            _visible_jokes_for_request(self.request)
            .values("submitter_name")
            .annotate(joke_count=Count("id"))
            .order_by("submitter_name")
        )


class SubmitterJokesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = JokeReadSerializer

    def get_queryset(self):
        submitter_name = self.kwargs["submitter_name"]
        return _visible_jokes_for_request(self.request).filter(submitter_name=submitter_name).order_by("-created_at")