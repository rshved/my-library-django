from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

import re
from django.utils.translation import gettext_lazy as _
# from twilio_sms.sms_client import SmsClient
from user import models as user_models
from user import enums as user_enums


def raise_400(detail=None):
    raise serializers.ValidationError(detail)


class CreateSmsSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17, write_only=True)
    detail = serializers.CharField(
        read_only=True, default="success", required=False)

    def create(self, validated_data):
        # client = SmsClient()
        # is_sent = client.send_sms_verification(validated_data["phone_number"])

        # if not is_sent:
        #     raise_400("Could not send verification sms")
        return {}

    def validate_phone_number(self, phone_number: str):
        is_valid = re.match("^\+?1?\d{9,15}$", phone_number)

        if is_valid is None:
            raise_400("Invalid phone number")
        return phone_number


class VerifySmsSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True, max_length=17)
    code = serializers.CharField(write_only=True)

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def create(self, validated_data):
        phone = validated_data["phone"]
        user = user_models.User.objects.filter(phone=phone).first()
        if user:
            user.is_phone_verified = True
            user.save()

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    def validate_phone_number(self, phone):
        is_valid = re.match("^\+?1?\d{9,15}$", phone)

        if is_valid is None:
            raise_400(_('Invalid phone number'))
        return phone

    def validate_code(self, code):
        # is_valid = SmsClient().check_sms_code(
        #     code=code,
        #     phone_number=self.initial_data.get("phone")
        # )
        # if not is_valid:
        #     raise_400(_('Invalid code'))
        return code
