from django.db import models

from ncjm.models import JokeBase


class LongJoke(JokeBase):
    title = models.TextField(
        help_text="The title of the joke.",
    )

    transcript = models.TextField(
        help_text="The text of the joke."
    )

    notes = models.TextField(
        help_text="Any notes about the joke.",
        blank=True,
        null=True,
    )

    hidden_notes = models.TextField(
        help_text="Any notes about the joke that should not be immediately visible",
        blank=True,
        null=True,
    )

    media_url = models.URLField(
        help_text="A URL to an audio or video recording of the joke.",
        blank=True,
        null=True,
    )

    def _get_content_field(self):
        """Returns the content field of the joke."""
        return self.title