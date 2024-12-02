from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist

from ncjm.models import Joke, Tag, JokeTag, Reaction
from admin.JokeTagInlineForm import JokeTagInlineForm

### actions for the admin panel
def approve_jokes(modeladmin, request, queryset):
    """
    Approves selected jokes in the admin panel.
    """
    queryset.update(is_approved=True)
approve_jokes.short_description = "Approve selected jokes"

def unapprove_jokes(modeladmin, request, queryset):
    """
    Un-approves selected jokes in the admin panel.
    """
    queryset.update(is_approved=False)
unapprove_jokes.short_description = "Un-approve selected jokes"

def hard_delete_jokes(modeladmin, request, queryset):
    """
    Hard-deletes selected jokes in the admin panel.
    """
    for joke_record in queryset:
        joke_record.hard_delete()
hard_delete_jokes.short_description = "Hard delete selected jokes"

### filters for the admin panel
class OrphanedJokesFilter(admin.SimpleListFilter):
    """
    Filters jokes that are not associated with any tags.
    """
    title = "Un-tagged jokes"
    parameter_name = "orphaned_jokes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(tags__isnull=True)
        if self.value() == "no":
            return queryset.filter(tags__isnull=False)
        return queryset

class OrphanedTagsFilter(admin.SimpleListFilter):
    """
    Filters tags that are not associated with any jokes.
    """
    title = "Un-joked tags"
    parameter_name = "orphaned_tags"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(joke__isnull=True)
        if self.value() == "no":
            return queryset.filter(joke__isnull=False)
        return queryset


### inline forms for the admin panel
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


### Admin classes
class JokeAdmin(admin.ModelAdmin):
    form = JokeTagInlineForm
    list_display = ("setup", "punchline", "submitter_name", "created_at", "is_approved", "is_deleted",)
    search_fields = ("setup", "punchline", "submitter_name",)
    list_filter = ("is_approved", "is_deleted", "created_at", OrphanedJokesFilter,)
    ordering = ("-created_at",)
    actions = [approve_jokes, unapprove_jokes, hard_delete_jokes,]

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

admin.site.register(Joke, JokeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(JokeTag, JokeTagAdmin)
admin.site.register(Reaction)