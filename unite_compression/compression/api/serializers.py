from django_ffmpeg.models import Video
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(required=False)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            "title",
            "video",
            "thumb",
            "description",
            "convert_status",
            "converted_at",
            "convert_extension",
        ]


class AsyncResultSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.JSONField()

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "status": instance.status,
            "result": instance.result,
        }
