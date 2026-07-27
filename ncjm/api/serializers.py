from rest_framework import serializers

from ncjm.models import Joke, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "tag_text", "created_at"]
        read_only_fields = ["id", "created_at"]


class TagWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "tag_text", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_tag_text(self, value):
        normalized = value.strip().lower()

        if len(normalized) < 3:
            raise serializers.ValidationError("Tag text must be at least 3 characters long.")

        queryset = Tag.objects.filter(tag_text__iexact=normalized)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("A tag with this text already exists.")

        return normalized


class JokeTagInputSerializer(serializers.Serializer):
    tag_text = serializers.CharField(max_length=100)

    def validate_tag_text(self, value):
        normalized = value.strip().lower()
        if len(normalized) < 3:
            raise serializers.ValidationError("Tag text must be at least 3 characters long.")
        return normalized


class JokeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Joke
        fields = [
            "id",
            "setup",
            "punchline",
            "submitter_name",
            "slug",
            "created_at",
            "is_approved",
            "tags",
            "reactions",
        ]


class JokeWriteSerializer(serializers.ModelSerializer):
    tags = JokeTagInputSerializer(many=True, required=False)

    class Meta:
        model = Joke
        fields = [
            "id",
            "setup",
            "punchline",
            "submitter_name",
            "is_approved",
            "tags",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        setup = attrs.get("setup", getattr(self.instance, "setup", None))
        punchline = attrs.get("punchline", getattr(self.instance, "punchline", None))

        if setup is not None and punchline is not None and setup.strip() == punchline.strip():
            raise serializers.ValidationError({"non_field_errors": ["Setup and punchline cannot be the same."]})

        return attrs

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        joke = Joke.objects.create(**validated_data)

        if not joke.reactions:
            joke.reactions = Joke.default_reactions.copy()
            joke.save(update_fields=["reactions"])

        self._set_tags(joke, tags_data)
        return joke

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags", None)

        for field in ["setup", "punchline", "submitter_name", "is_approved"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()

        if tags_data is not None:
            self._set_tags(instance, tags_data, replace=True)

        return instance

    @staticmethod
    def _set_tags(joke, tags_data, replace=False):
        if replace:
            joke.tags.clear()

        for tag_data in tags_data:
            tag_text = tag_data["tag_text"].strip().lower()
            tag_record, _ = Tag.objects.get_or_create(tag_text=tag_text)
            joke.tags.add(tag_record)


class ReactionInputSerializer(serializers.Serializer):
    emoji = serializers.CharField(max_length=8)

    def validate_emoji(self, value):
        normalized = value.strip()

        if normalized not in Joke.default_reactions:
            raise serializers.ValidationError("Invalid reaction emoji.")

        return normalized


class SubmitterSerializer(serializers.Serializer):
    submitter_name = serializers.CharField()
    joke_count = serializers.IntegerField()