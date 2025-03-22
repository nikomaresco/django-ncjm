from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError

class AlreadyReactedException(Exception):
    """
    Raised when a user tries to react to a joke more than once.
    """
    pass

class JokeBase(models.Model):
    default_reactions = {
        "😠": 0,
        "🥱": 0,
        "🫤": 0,
        "🙄": 0,
        "🤣": 0,
        "🤩": 0,
    }

    created_at = models.DateTimeField(
        help_text="The date and time the joke was submitted.",
        auto_now_add=True
    )

    is_approved = models.BooleanField(
        help_text="Whether the joke has been moved from the approval queue to the main joke list.",
        default=False,
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

    is_deleted = models.BooleanField(
        help_text="Whether the joke has been deleted.",
        default=False,
    )

    tags = models.ManyToManyField(
        "Tag",
        help_text="The tags associated with the joke.",
        through="JokeTag",
        related_name="jokes",
        related_query_name="joke",
    )

    """
    Reactions are stored in a JSON field as a dictionary of emoji labels and
    counts.

    I chose this implementation because there's not really any reason to store
    individual reactions in the database; this saves on lookups and should be
    more efficient in the long run.
    """
    reactions = models.JSONField(
        help_text="The reactions to the joke stored as totals.",
        default=dict,
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

    @staticmethod
    def is_slug_unique(
        slug: str,
    ) -> bool:
        """
        Checks if the slug is unique.

        Args:
            slug (str): The slug to check.

        Returns:
            bool: True if the slug is unique, False otherwise.
        """
        return not JokeBase.objects.filter(slug=slug).exists()

    def clean(self):
        """
        Ensures that the setup and punchline are not the same, and that a
        default reactions dictionary is present.
        """
        if self.setup == self.punchline:
            raise ValidationError("Setup and punchline cannot be the same.")
        if not self.reactions or self.reactions == {}:
            self.reactions = self.default_reactions.copy()

    @staticmethod
    def _get_content_field(self):
        """Returns the content field of the joke."""
        raise NotImplementedError("Subclasses must implement this method.")

    def save(self, *args, **kwargs):
        """
        Saves the joke instance.

        Updates the slug if the setup has changed or if the slug is not set.
        """
        content_value = self._get_content_field()
        slug_has_changed = content_value != JokeBase.objects.get(pk=self.pk)._get_content_field
        
        if not self.slug or slug_has_changed:
            new_slug = slugify(content_value)

            # truncate the slug to the max field length
            max_length = self._meta.get_field("slug").max_length
            new_slug = new_slug[:max_length]

            # ensure the slug is unique by appending a counter if necessary
            slug_counter = 1
            while not JokeBase.is_slug_unique(new_slug):
                new_slug = f"{new_slug}-{slug_counter}"
                slug_counter += 1

            self.slug = new_slug
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Soft-deletes the joke instance by setting `is_deleted` to True.
        """
        self.is_deleted = True
        self.save()

    def hard_delete(self, *args, **kwargs):
        """
        Hard-deletes the joke instance and any tags that would be orphaned by
        the deletion.
        """
        # check for orphaned tags and delete them
        for tag in self.tags.all():
            if not tag.jokes.exclude(id=self.id).exists():
                tag.delete()
        # delete the joke
        super(JokeBase, self).delete(*args, **kwargs)

    def add_reaction(self,
        reaction_emoji: str,
        ip_address: str,
        user_agent: str,
    ):
        """
        Adds a reaction to the joke.

        Args:
            reaction_emoji (str): The emoji of the reaction.
            ip_address (str): The IP address of the user who reacted.
            user_agent (str): The user agent string of the browser used.
        """
        from ncjm.models import ReactionTracker

        if self.is_deleted:
            raise ValidationError("Cannot react to a deleted joke.")
        
        if ReactionTracker.objects.filter(
            joke=self,
            ip_address=ip_address,
            user_agent=user_agent,
        ).exists():
            raise AlreadyReactedException("You have already reacted to this joke.")

        if reaction_emoji not in self.default_reactions.keys():
            raise ValidationError(f"Invalid reaction emoji.")

        ReactionTracker.objects.create(
            joke=self,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if reaction_emoji in self.reactions:
            self.reactions[reaction_emoji] += 1
        else:
            self.reactions[reaction_emoji] = 1

        self.save()