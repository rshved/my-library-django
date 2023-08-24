from celery import shared_task

from user import models as user_models
from mail import handlers


@shared_task(name="send_verify_email")
def send_verify_email_task(user_id: int, code: str):
    user = user_models.User.objects.filter(id=user_id).first()
    if user is None:
        return
    handlers.verify_email_handler(user, code)


@shared_task(name="send_password_reset_request_email")
def send_password_reset_request_email_task(user_id: int, code: str):
    user = user_models.User.objects.filter(id=user_id).first()
    if user is None:
        return

    handlers.password_reset_request_handler(user, code)
