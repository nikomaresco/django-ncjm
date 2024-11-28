from django.db import models
from django.utils.text import slugify

class Joke(models.Model):
    created_at = models.DateTimeField(
        help_text="The date and time the joke was submitted.",
        auto_now_add=True
    )

    is_approved = models.BooleanField(
        help_text="Whether the joke has been moved from the approval queue to the main joke list.",
        default=False,
    )

    setup = models.TextField(
        help_text="The setup of the joke."
    )

    punchline = models.TextField(
        help_text="The punchline of the joke.",
    )

    submitter_name = models.CharField(
        help_text="The name of the person who submitted the joke.",
        max_length=255,
    )

    slug = models.SlugField(
        help_text="The slugified version of the joke setup.",
        unique=True,
        max_length=255,
        editable=False,
    )

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["id"]),
            models.Index(fields=["submitter_name"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_slug")
        ]

    def __str__(self):
        """
        Returns a string representation of the joke.
        """
        return f"{self.setup} - {self.punchline}"

    def is_slug_unique(self,
        slug: str,
    ) -> bool:
        """
        Checks if the slug is unique.

        Args:
            slug (str): The slug to check.

        Returns:
            bool: True if the slug is unique, False otherwise.
        """
        return not Joke.objects.filter(slug=slug).exists()

    def save(self, *args, **kwargs):
        """
        Saves the joke instance.

        Updates the slug if the setup has changed or if the slug is not set.
        """
        if not self.slug or self.setup != Joke.objects.get(pk=self.pk).setup:
            new_slug = slugify(self.setup)
            if self.is_slug_unique(new_slug):
                self.slug = new_slug
        super().save(*args, **kwargs)