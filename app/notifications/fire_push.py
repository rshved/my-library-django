import firebase_admin
from firebase_admin.messaging import Message, Notification, send

from notifications.schemas import FirePush

push_app = firebase_admin.initialize_app()

# !!! DOCS: https://github.com/firebase/firebase-admin-python/blob/master/snippets/messaging/cloud_messaging.py


def send_push(fire_push: FirePush):
    if not fire_push.data.get('click_action'):
        fire_push.data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

    message = Message(
        notification=Notification(
            title=fire_push.title,
            body=fire_push.body,
        ),
        token=fire_push.push_id,
        data=fire_push.data
    )

    send(message)

  # TODO: add notification model
