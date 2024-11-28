from django.db import models
from django.utils import timezone

from ncjm.models import Joke, Reaction

class ReactionTracker(models.Model):
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="The date and time when the reaction was made"
    )

    joke = models.ForeignKey(
        Joke,
        on_delete=models.CASCADE,
        help_text="The joke that received the reaction"
    )

    reaction = models.ForeignKey(
        Reaction,
        on_delete=models.CASCADE,
        help_text="The reaction given to the joke"
    )

    ip_address = models.GenericIPAddressField(
        help_text="The IP address of the user who reacted"
    )

    user_agent = models.CharField(
        max_length=255,
        help_text="The user agent string of the browser used"
    )

    class Meta:
        unique_together = (
            "joke",
            "reaction",
            "ip_address",
            "user_agent"
        )

        indexes = [
            models.Index(fields=[
                "joke",
                "reaction",
                "ip_address",
                "user_agent"
            ])
        ]

    def __str__(self):
        return f"Reaction to {self.joke} by {self.ip_address} at {self.created_at}"