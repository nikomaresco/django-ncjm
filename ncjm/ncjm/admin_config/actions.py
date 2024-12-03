
#TODO: should these go into a class as static methods?

def joke__approve_jokes(modeladmin, request, queryset):
    """
    Approves selected jokes in the admin panel.
    """
    queryset.update(is_approved=True)
joke__approve_jokes.short_description = "Approve selected jokes"

def joke__unapprove_jokes(modeladmin, request, queryset):
    """
    Un-approves selected jokes in the admin panel.
    """
    queryset.update(is_approved=False)
joke__unapprove_jokes.short_description = "Un-approve selected jokes"

def joke__hard_delete_jokes(modeladmin, request, queryset):
    """
    Hard-deletes selected jokes in the admin panel.
    """
    for joke_record in queryset:
        joke_record.hard_delete()
joke__hard_delete_jokes.short_description = "Hard delete selected jokes"
