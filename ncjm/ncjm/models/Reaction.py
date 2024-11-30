from django.db import models

from ncjm.models import Joke

class Reaction(models.Model):
    label = models.CharField(
        help_text="The emoji label for the reaction.",
        max_length=10,
    )

    joke = models.ForeignKey(
        Joke,
        help_text="The joke to which this reaction is attached.",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.label