from django.contrib import admin


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