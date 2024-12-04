from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist

from ncjm.models import Joke, Tag, JokeTag
from .JokeTagInlineForm import JokeTagInlineForm
from .filters import OrphanedJokesFilter, OrphanedTagsFilter
from .inlines import JokeInline
from .actions import joke__approve_jokes, joke__unapprove_jokes, joke__hard_delete_jokes

### Admin classes
class JokeAdmin(admin.ModelAdmin):
    form = JokeTagInlineForm
    readonly_fields = ("slug",)
    list_display = ("setup", "punchline", "submitter_name", "created_at", "is_approved", "is_deleted",)
    search_fields = ("setup", "punchline", "submitter_name",)
    list_filter = ("is_approved", "is_deleted", "created_at", OrphanedJokesFilter,)
    ordering = ("-created_at",)
    actions = [joke__approve_jokes, joke__unapprove_jokes, joke__hard_delete_jokes,]

    def get_queryset(self, request):
        """
        Override get_queryset to exclude soft-deleted jokes from the default
        queryset.
        """
        jokes_queryset = super().get_queryset(request)
        if not request.GET.get("is_deleted__exact"):
            return jokes_queryset.filter(is_deleted=False)
        return jokes_queryset

    def get_object(self, request, joke_id, from_field=None):
        """
        Override get_object to include soft-deleted jokes.
        """
        try:
            obj = Joke._default_manager.get(pk=joke_id)
        except ObjectDoesNotExist:
            obj = Joke.objects.none()
        return obj

    def delete_queryset(self, request, jokes_queryset):
        """
        Soft-deletes the a queryset of selected jokes.
        """
        for joke_record in jokes_queryset:
            joke_record.delete()

    def delete_model(self, request, joke_record):
        """
        Soft-deletes a single selected joke.
        """
        joke_record.delete()

class TagAdmin(admin.ModelAdmin):
    list_display = ("tag_text", "ext_id",)
    search_fields = ("tag_text",)
    ordering = ("tag_text",)
    list_filter = (OrphanedTagsFilter,)
    inlines = [JokeInline,]

class JokeTagAdmin(admin.ModelAdmin):
    list_display = ("joke", "tag", "created_at",)
    search_fields = ("joke__setup", "tag__tag_text",)
    ordering = ("-created_at",)

