import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("unite_compression")


# https://stackoverflow.com/questions/9824172/find-out-whether-celery-task-exists
# @after_task_publish.connect
# def update_sent_state(sender=None, body=None, **kwargs):
#     # the task may not exist if sent using `send_task` which
#     # sends tasks by name, so fall back to the default result backend
#     # if that is the case.
#     from celery.signals import after_task_publish
#     task = app.tasks.get(sender)
#     backend = task.backend if task else app.backend

#     backend.store_result(body["id"], None, "SENT")


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
