from django.db import models
from django.core.exceptions import ValidationError

class Tag(models.Model):
    created_at = models.DateTimeField(
        help_text="The date and time the tag was created.",
        auto_now_add=True,
    )

    tag_text = models.CharField(
        help_text="The tag text.",
        max_length=100,
        unique=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tag_text"],
                name="unique_tag_text"
            )
        ]

    def __str__(self):
        return self.tag_text

    def clean(self):
        """
        Validate `tag_text` for length and case-insensitive uniqueness.
        """
        if len(self.tag_text) < 3:
            raise ValidationError("Tag text must be at least 3 characters long.")

        if Tag.objects.filter(tag_text__iexact=self.tag_text) \
            .exclude(pk=self.pk).exists():
            raise ValidationError(f"Tag with tag_text '{self.tag_text}' already exists.")

    def save(self, *args, **kwargs):
        """
        Saves the Tag, forcing `tag_text` to lowercase.
        """
        self.tag_text = self.tag_text.lower()
        self.clean()
        super().save(*args, **kwargs)