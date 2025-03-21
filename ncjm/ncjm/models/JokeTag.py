from django.db import models

from ncjm.models import JokeBase, Tag

class JokeTag(models.Model):
    created_at = models.DateTimeField(
        help_text="The date and time when the joke was tagged",
        auto_now_add=True,
    )

    joke = models.ForeignKey(
        JokeBase,
        help_text="The joke that was tagged",
        on_delete=models.CASCADE,
    )

    tag = models.ForeignKey(
        Tag,
        help_text="The tag that was added to the joke",
        on_delete=models.CASCADE,
    )

    class Meta:
        indexes = [
            models.Index(fields=["joke"]),
            models.Index(fields=["tag"]),
            models.Index(fields=["joke", "tag"]),
        ]
        unique_together = ("joke", "tag")

    def __str__(self):
        return f"{self.joke} - {self.tag}"
