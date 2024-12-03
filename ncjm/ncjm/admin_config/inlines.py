from django.contrib import admin

from ncjm.models import Joke

class JokeInline(admin.TabularInline):
    """
    Displays the associated jokes for a tag in the admin panel.
    """
    model = Joke.tags.through
    extra = 0
    verbose_name = "Associated Joke"
    verbose_name_plural = "Associated Jokes"
    fields = ("joke",)
    readonly_fields = ("joke",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False