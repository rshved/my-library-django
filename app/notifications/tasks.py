from celery import shared_task


from notifications.schemas import FirePush
from notifications import fire_push


@shared_task(name='send_fire_push')
def send_fire_push_task(fire_push_schema: FirePush):

    fire_push.send_push(fire_push_schema)
