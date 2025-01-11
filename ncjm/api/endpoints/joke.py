import random
import logging

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ncjm.models import Joke
from ..serializers import JokeSerializer

logger = logging.getLogger(__name__)


def _get_joke(request):
    joke_id = request.query_params.get("id")
    joke_slug = request.query_params.get("slug")

    if joke_id:
        return get_object_or_404(Joke, id=joke_id)
    if joke_slug:
        return get_object_or_404(Joke, slug=joke_slug)

    jokes = Joke.objects.all()
    if jokes:
        joke = random.choice(jokes)
        serializer = JokeSerializer(joke)
        return Response(serializer.data)

    return Response({
            "message": "No jokes available"
        },
        status=status.HTTP_404_NOT_FOUND
    )

def _create_joke(request):
    serializer = JokeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({
            "message": "Validation error",
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST
    )

def _update_joke(request):
    joke_id = request.query_params.get("id")
    joke = get_object_or_404(Joke, id=joke_id)
    serializer = JokeSerializer(joke, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response({
            "message": "Validation Error",
            "errors": serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST
    )

def _delete_joke(request):
    joke_id = request.query_params.get("id")
    joke = get_object_or_404(Joke, id=joke_id)
    joke.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def create_read_joke(request):
    if request.method == "GET":
        return _get_joke(request)
    if request.method == "POST":
        return _create_joke(request)

@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def update_delete_joke(request):
    if request.method == "PATCH":
        return _update_joke(request)
    if request.method == "DELETE":
        return _delete_joke(request)