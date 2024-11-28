import random
import logging

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from ncjm.models import Joke
from ..serializers import JokeSerializer

logger = logging.getLogger(__name__)


@api_view(["GET"])
def get_random_joke(request):
    jokes = Joke.objects.all()
    if jokes:
        joke = random.choice(jokes)
        serializer = JokeSerializer(joke)
        return Response(serializer.data)
    return Response({"message": "No jokes available"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
def get_joke_by_id(request):
    joke_id = request.query_params.get('id')
    joke = get_object_or_404(Joke, id=joke_id)
    serializer = JokeSerializer(joke)
    return Response(serializer.data)

@api_view(["GET"])
def get_joke_by_slug(request, slug):
    joke = get_object_or_404(Joke, slug=slug)
    serializer = JokeSerializer(joke)
    return Response(serializer.data)

@api_view(["DELETE"])
def delete_joke(request):
    joke_id = request.query_params.get('id')
    joke = get_object_or_404(Joke, id=joke_id)
    joke.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["POST"])
def create_joke(request):
    serializer = JokeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["PATCH"])
def update_joke(request):
    joke_id = request.query_params.get('id')
    joke = get_object_or_404(Joke, id=joke_id)
    serializer = JokeSerializer(joke, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)