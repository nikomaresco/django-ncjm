from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from ncjm.models import Joke
from ..serializers import JokeSerializer

def _get_jokes_by_submitter(request, submitter_name):
    jokes = Joke.objects.filter(submitter_name=submitter_name)

    page = request.query_params.get("page", 1)
    per_page = request.query_params.get("per_page", 10)

    paginator = Paginator(jokes, per_page=per_page)
    jokes_paginated = paginator.get_page(page)

    serializer = JokeSerializer(jokes_paginated, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_jokes_by_submitter(request, submitter_name):
    return _get_jokes_by_submitter(request, submitter_name)