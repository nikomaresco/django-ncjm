from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from ncjm.models import AlreadyReactedException, Joke
from ..exceptions import ConflictError
from ..serializers import ReactionInputSerializer


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class JokeReactionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = ReactionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        joke = get_object_or_404(Joke, pk=pk, is_deleted=False)

        emoji = serializer.validated_data["emoji"]
        ip_address = _get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            joke.add_reaction(
                reaction_emoji=emoji,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except AlreadyReactedException as exc:
            raise ConflictError(str(exc)) from exc
        except DjangoValidationError as exc:
            raise ValidationError(str(exc)) from exc

        return Response(
            {
                "message": "Reaction recorded.",
                "reactions": joke.reactions,
            },
            status=status.HTTP_201_CREATED,
        )


class AllowedReactionsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        return Response(
            {"allowed_reactions": settings.NCJM_ALLOWED_REACTIONS},
            status=status.HTTP_200_OK,
        )