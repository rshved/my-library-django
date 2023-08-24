from celery import shared_task


from notifications.schemas import FirePush
from notifications import fire_push_sender


@shared_task(name='send_fire_push')
def send_fire_push_task(fire_push_schema: FirePush):

    fire_push_sender.send_push(fire_push_schema)
