import os
import settings
from typing import Optional

from django.core.mail import EmailMultiAlternatives
from anymail.message import attach_inline_image_file, attach_inline_image


from mail.models import Mail
from user.models import User


# ------------  Single sender ------------- #
def single_sender_wrapper(subject: str, body: str, email: str, name: Optional[str] = '') -> bool:
    """
        Sender wrapper
    """
    recepient = ''
    if name:
        recepient = f'{name} <{email}>'
    else:
        recepient = email

    # Message object
    msg = EmailMultiAlternatives(
        subject, body,
        f'{settings.PROJECT_NAME} <{settings.DEFAULT_EMAIL_FROM}>',
        [recepient],
        headers={
            'List-Unsubscribe': f'{settings.FRONTEND_URL}/unsubscribe/{email}',
        }
    )

    # Add the logo as a header for CID usage
    with open('mail/templates/files/logo.png', 'rb') as logo_file:
        logo_data = logo_file.read()
        logo_cid = attach_inline_image(
            msg, logo_data, 'logo.png', 'logo_cid')
        body = body.replace('{{ logo }}', logo_cid)
        msg.body = body

    # Alternative
    msg.attach_alternative(body, 'text/html')

    # Await result from sender provider
    try:
        result = msg.send()
        print('result: ', result)
        return True
    except Exception as e:
        print('Error: ', e)
        return False


# --------------  Helpers ---------------- #
def body_replace(body, variables):
    """
       Replace variables in templates
    """
    new_body = body
    for key, value in variables.items():
        new_body = new_body.replace(str(key), str(value))
        print('new_body: ', new_body)
    return new_body


def create_model(subject: str, body: str, email: str, user: Optional[User] = None) -> Mail:
    """
       Create Mail model 
    """
    mail = Mail.objects.create(
        user=user,
        subject=subject,
        body=body,
        email=email,
    )
    mail.save()
    return mail


# --------------  Handlers ---------------- #
def verify_email_handler(user: User, code: str, url=f'{settings.FRONTEND_VERIFY_EMAIL_URL}'):
    """
       Send verification code for verify email
    """
    SUBJECT = f'Verify you email for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/verify_email.html'

    # Load the email template
    with open(TEMPLATE, 'r') as f:
        body = f.read()

    # Variables for replace
    variables = {
        '{{code}}': code,
        '{{url}}': url,
    }

    body = body_replace(body, variables)

    mail = create_model(SUBJECT, body, user.email, user)

    res = single_sender_wrapper(SUBJECT, body, user.email,
                                f'{user.name} {user.surname}')

    if res:
        mail.is_send = True
        mail.save()


def password_reset_request_handler(user: User, code: str, url=f'{settings.FRONTEND_VERIFY_EMAIL_URL}'):
    """
       Send verification code for reset password
    """
    SUBJECT = f'Reset your password for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/reset_password.html'

    # Load the email template
    with open(TEMPLATE, 'r') as f:
        body = f.read()

    # Variables for replace
    print('code: ', code)
    variables = {
        '{{code}}': code,
        '{{url}}': url,
    }

    print('body: 1: ', body)
    body = body_replace(body, variables)
    print('body: 2: ', body)

    mail = create_model(SUBJECT, body, user.email, user)

    res = single_sender_wrapper(SUBJECT, body, user.email,
                                f'{user.name} {user.surname}')

    if res:
        mail.is_send = True
        mail.save()
