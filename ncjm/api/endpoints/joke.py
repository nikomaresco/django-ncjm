import random

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from ncjm.models import Joke
from ..serializers import JokeReadSerializer, JokeWriteSerializer


def _base_queryset_for_read(request):
    queryset = Joke.objects.filter(is_deleted=False).prefetch_related("tags")

    if request.user.is_authenticated and request.user.is_staff:
        return queryset

    return queryset.filter(is_approved=True)


class JokeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Joke.objects.filter(is_deleted=False).prefetch_related("tags")

        if self.request.method == "GET":
            queryset = _base_queryset_for_read(self.request)

        submitter_name = self.request.query_params.get("submitter")
        tag_text = self.request.query_params.get("tag")
        approved = self.request.query_params.get("approved")

        if submitter_name:
            queryset = queryset.filter(submitter_name=submitter_name)

        if tag_text:
            queryset = queryset.filter(tags__tag_text__iexact=tag_text)

        if approved is not None and self.request.user.is_authenticated and self.request.user.is_staff:
            normalized = approved.strip().lower()
            if normalized in ["true", "1", "yes"]:
                queryset = queryset.filter(is_approved=True)
            elif normalized in ["false", "0", "no"]:
                queryset = queryset.filter(is_approved=False)

        return queryset.order_by("-created_at").distinct()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return JokeWriteSerializer
        return JokeReadSerializer

    def create(self, request, *args, **kwargs):
        write_serializer = JokeWriteSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        joke = write_serializer.save()
        read_serializer = JokeReadSerializer(joke, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class JokeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        queryset = Joke.objects.filter(is_deleted=False).prefetch_related("tags")

        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return _base_queryset_for_read(self.request)

        return queryset

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return JokeWriteSerializer
        return JokeReadSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = JokeWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        joke = serializer.save()
        read_serializer = JokeReadSerializer(joke, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        joke = self.get_object()
        hard_delete = request.query_params.get("hard", "false").strip().lower() in ["true", "1", "yes"]

        if hard_delete:
            if not request.user.is_staff:
                raise PermissionDenied("Only staff users can hard delete jokes.")
            joke.hard_delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        joke.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RandomJokeView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        jokes = list(_base_queryset_for_read(request))

        if not jokes:
            raise NotFound("No jokes available")

        joke = random.choice(jokes)
        serializer = JokeReadSerializer(joke)
        return Response(serializer.data, status=status.HTTP_200_OK)