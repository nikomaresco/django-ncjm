from django.contrib import admin

from ncjm.models import CornyJoke, Tag, JokeTag
from .admin_config.admin import JokeAdmin, TagAdmin, JokeTagAdmin


admin.site.register(CornyJoke, JokeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(JokeTag, JokeTagAdmin)