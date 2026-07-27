from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from ncjm.models import Joke, Tag
from ..serializers import JokeReadSerializer, TagSerializer, TagWriteSerializer


def _visible_jokes_for_request(request):
    queryset = Joke.objects.filter(is_deleted=False).prefetch_related("tags")

    if request.user.is_authenticated and request.user.is_staff:
        return queryset

    return queryset.filter(is_approved=True)


class TagListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Tag.objects.all().order_by("tag_text")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TagWriteSerializer
        return TagSerializer


class TagRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Tag.objects.all().order_by("tag_text")

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return TagWriteSerializer
        return TagSerializer


class TagJokesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = JokeReadSerializer

    def get_queryset(self):
        tag_text = self.kwargs["tag_text"]
        tag = get_object_or_404(Tag, tag_text__iexact=tag_text)
        return _visible_jokes_for_request(self.request).filter(tags=tag).order_by("-created_at")
