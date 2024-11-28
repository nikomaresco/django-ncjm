from django.db import models
from ncjm.models import Joke

class Tag(models.Model):
    joke = models.ForeignKey(
        Joke,
        help_text="The joke to which this tag is attached.",
        on_delete=models.CASCADE,
    )

    tag_text = models.TextField(
        help_text="The tag text.",
        unique=True,  # Enforce unique constraint on tag_text
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tag_text", "joke"],
                name="unique_tag_text_joke"
            )
        ]

    def __str__(self):
        return self.tag_text