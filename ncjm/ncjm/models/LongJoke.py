from django.db import models

from ncjm.models import JokeBase


class LongJoke(JokeBase):
    transcript = models.TextField(
        help_text="The text of the joke."
    )

    media_url = models.URLField(
        help_text="A URL to an audio or video recording of the joke.",
    )
