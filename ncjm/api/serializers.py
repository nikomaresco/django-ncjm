from rest_framework import serializers
from ncjm.models import Joke

class JokeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Joke
        fields = "__all__"