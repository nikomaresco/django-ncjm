from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from ncjm.models import Tag, Joke
from ..serializers import TagSerializer, JokeSerializer


def _get_jokes_with_tag(request, tag_text):
    tag = get_object_or_404(Tag, tag_text=tag_text)
    jokes = Joke.objects.filter(tags=tag)

    page = request.query_params.get("page", 1)
    per_page = request.query_params.get("per_page", 10)

    paginator = Paginator(jokes, per_page=per_page)
    jokes_paginated = paginator.get_page(page)

    serializer = JokeSerializer(jokes_paginated, many=True)
    return Response(serializer.data)

def _delete_tag(request, tag_text):
    tag = get_object_or_404(Tag, tag_text=tag_text)
    tag.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

def _create_tag(request):
    serializer = TagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def get_or_delete_tag(request, tag_text):
    if request.method == "GET":
        return _get_jokes_with_tag(request, tag_text)
    if request.method == "DELETE":
        return _delete_tag(request, tag_text)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_tag(request):
    return _create_tag(request)
