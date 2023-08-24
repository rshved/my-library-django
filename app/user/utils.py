from django.utils.translation import gettext_lazy as _
from requests import Request
import random
import string
import re
import settings
import redis
from rest_framework.serializers import ValidationError
# import phonenumbers


def is_valid_password(password_candidate):
    if len(password_candidate) < 8:
        raise ValidationError(_("Password must be at least 8 symbols"))
    if re.search('[0-9]', password_candidate) is None:
        raise ValidationError(_("Password must have at least 1 digit"))
    if re.search('[a-z]', password_candidate) is None and re.search('[A-Z]', password_candidate) is None:
        raise ValidationError(
            _("Password must have at least 1 character in lowercase or uppercase"))
    return True


# def is_valid_phone(phone_candidate):
#     try:
#         parsed_phone = phonenumbers.parse(phone_candidate, None)
#         if phonenumbers.is_valid_number(parsed_phone):
#             return True
#         else:
#             response.bad_request(_('Invalid phone number'))
#     except Exception as e:
#         response.bad_request(_('Invalid phone number'))


redis_instance = redis.StrictRedis(
    host=settings.REDIS_SERVER,
    password=settings.REDIS_PASSWORD,
    port=settings.REDIS_PORT,
    db=settings.REDIS_APP_DB
)


def generate_verification_code(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def set_verification_code(code, code_type, user_id):
    code_key = f"{code_type}:{code}"
    setuped_code = redis_instance.set(
        code_key,
        user_id,
        ex=settings.RESET_CODE_EXPIRE
    )
    return code_key


def compare_verification_code(code, code_type):
    code_key = f"{code_type}:{code}"
    code = redis_instance.get(code_key)
    return code.decode() if code else None


def get_verification_code(code, code_type):
    code_key = f"{code_type}:{code}"
    code = redis_instance.get(code_key)
    return code.decode() if code else None


def delete_used_code(code, code_type):
    code_key = f"{code_type}:{code}"
    deleted_code = redis_instance.delete(code_key)
    return deleted_code


def get_device_id_from_request(request: Request) -> str:
    return request.headers.get('Accept-Device-Application')
