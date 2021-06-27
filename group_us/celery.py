import os

from celery import Celery

from group_us import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'group_us.settings')

app = Celery(
    'group_us',
    broker=
    f"amqp://{os.getenv('RABBITMQ_USERNAME')}:"
    f"{os.getenv('RABBITMQ_PASSWORD')}"
    f"@{os.getenv('RABBITMQ_HOST')}",
    include=["api.tasks"]
)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
