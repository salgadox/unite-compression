from django.conf import settings
from django.contrib.auth import authenticate, login
from django_ffmpeg.models import ConvertingCommand, Video
from django_ffmpeg.tasks import convert_video
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AsyncResultSerializer, LoginSerializer, VideoSerializer


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = authenticate(
            request, username=data["username"], password=data["password"]
        )
        if user is not None:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            # Return user data
            return Response({"user": user.id})
        else:
            return Response(
                {"error": "Invalid login credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class VideoViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    queryset = Video.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=["GET"])
    def tasks(self, request, pk):
        # Check if there are any existing tasks for the new model instance
        existing_tasks = convert_video.AsyncResult(str(pk))
        serializer = AsyncResultSerializer(existing_tasks)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
        url_path=r"generate_link(?:/(?P<expire>\d+)/)",
    )
    def generate_link(self, request, pk, expire=None):
        def cdn_url(value):
            # https://github.com/jschneier/django-storages/issues/944
            if settings.AWS_S3_ENDPOINT_URL in value:
                cdn_domain = "https://" + settings.AWS_S3_CUSTOM_DOMAIN
                new_url = value.replace(settings.AWS_S3_ENDPOINT_URL, cdn_domain)
                return new_url
            else:
                return value

        video = self.queryset.get(pk=pk)
        bucket = video.video.storage.bucket
        if expire is None:
            expire = video.video.storage.querystring_expire
        url = bucket.meta.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket.name, "Key": video.video.name},
            ExpiresIn=expire,
        )
        return Response({"url": cdn_url(url)}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def convert(self, request, pk):
        command_id = ConvertingCommand.objects.first().id

        # Check if there are any existing tasks for the new model instance
        # task = convert_video.AsyncResult(str(pk))
        video = self.queryset.get(pk=pk)

        if video.convert_status == "pending":
            # If no task exists, create a new task and return it
            task = convert_video.delay(command_id, pk)
            serializer = AsyncResultSerializer(task)
            return Response(
                {"task": serializer.data, "message": "Task created"},
                status=status.HTTP_201_CREATED,
            )
        else:
            if video.convert_status == "started":
                # Task exists, return message and status
                message = "Video conversion in progress"
                _status = status.HTTP_204_NO_CONTENT
            if video.convert_status == "converted":
                # Video has been converted, return message and status
                message = "Video has been converted"
                _status = status.HTTP_204_NO_CONTENT
            else:
                message = "Video conversion error"
                _status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response(
                {"message": message},
                status=_status,
            )
