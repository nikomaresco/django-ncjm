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

    ext_id = models.IntegerField(
        help_text="The external ID of the tag.",
        null=True,
        blank=True,
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
        Validate the tag text for case-insensitive uniqueness.
        """
        if Tag.objects.filter(tag_text__iexact=self.tag_text) \
            .exclude(pk=self.pk).exists():
            raise ValidationError(f"Tag with text '{self.tag_text}' already exists.")


    def save(self, *args, **kwargs):
        """
        Save the tag text in lowercase.
        """
        self.tag_text = self.tag_text.lower()
        self.clean()
        super().save(*args, **kwargs)