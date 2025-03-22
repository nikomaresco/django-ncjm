from django.contrib import admin

from ncjm.models import CornyJoke, LongJoke

class JokeBaseInline(admin.TabularInline):
    """
    Displays the associated jokes for a tag in the admin panel.
    """
    extra = 0
    verbose_name = "Associated Joke"
    verbose_name_plural = "Associated Jokes"
    fields = ("joke",)
    readonly_fields = ("joke",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
class CornyJokeInline(JokeBaseInline):
    model = CornyJoke.tags.through

    def joke(self, instance):
        return instance.cornyjoke.setup

class LongJokeInline(JokeBaseInline):
    model = LongJoke.tags.through

    def joke(self, instance):
        return instance.longjoke.title