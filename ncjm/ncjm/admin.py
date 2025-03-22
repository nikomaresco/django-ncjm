from django.contrib import admin

from ncjm.models import LongJoke, CornyJoke, Tag, JokeTag
from .admin_config.admin import CornyJokeAdmin, LongJokeAdmin, TagAdmin, JokeTagAdmin


admin.site.register(CornyJoke, CornyJokeAdmin)
admin.site.register(LongJoke, LongJokeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(JokeTag, JokeTagAdmin)