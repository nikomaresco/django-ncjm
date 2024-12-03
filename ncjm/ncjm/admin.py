from django.contrib import admin

from ncjm.models import Joke, Tag, JokeTag, Reaction
from .admin_config.admin import JokeAdmin, TagAdmin, JokeTagAdmin


admin.site.register(Joke, JokeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(JokeTag, JokeTagAdmin)
admin.site.register(Reaction)