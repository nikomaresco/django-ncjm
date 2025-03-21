from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from ncjm.models import Tag, CornyJoke
from ..serializers import ReactionSerializer