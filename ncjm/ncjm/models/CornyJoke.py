from django.db import models

from ncjm.models import JokeBase


class CornyJoke(JokeBase):
    setup = models.TextField(
        help_text="The setup of the joke."
    )

    punchline = models.TextField(
        help_text="The punchline of the joke.",
    )

def _get_content_field(self):
    """Returns the content field of the joke."""
    return self.setup