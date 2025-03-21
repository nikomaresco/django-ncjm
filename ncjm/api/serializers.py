from rest_framework import serializers

from ncjm.models import CornyJoke, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "tag_text",
        ]

class JokeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = CornyJoke
        fields = [
            "id",
            "setup",
            "punchline",
            "submitter_name",
            "tags",
            "reactions"
        ]

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])

        joke = CornyJoke.objects.create(**validated_data)

        # add tags to the joke
        for tag_data in tags_data:
            tag_record, _ = Tag.objects.get_or_create(**tag_data)
            joke.tags.add(tag_record)
        return joke

    def update(self, joke_record, validated_data):
        tags_data = validated_data.pop("tags", [])

        # update the record either from the incoming validated_data or from the existing joke_record
        joke_record.setup = validated_data.get("setup", joke_record.setup)
        joke_record.punchline = validated_data.get("punchline", joke_record.punchline)
        joke_record.submitter_name = validated_data.get("submitter_name", joke_record.submitter_name)
        joke_record.save()

        # replace existing tags with new tags
        if tags_data:
            joke_record.tags.clear()
            for tag_data in tags_data:
                tag_record, _ = Tag.objects.get_or_create(tag_text=tag_data["tag_text"])
                joke_record.tags.add(tag_record)

        return joke_record