from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from typing import Tuple, Optional
from celery import current_app as celery_app
# from twilio_sms.sms_client import SmsClient

from core import response, exception
from user import models
from user import utils
from user import enums


class EmailRegistration(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    detail = serializers.CharField(
        read_only=True, default='success', required=False)

    def validate(self, attrs):
        user = models.User.objects.filter(
            email=attrs['email']
        ).first()
        if user:
            raise ValidationError(_('User already registered'))
        password_candidate = attrs['password']
        utils.is_valid_password(password_candidate)

        # IF NEED
        # device_id = utils.get_device_id_from_request(self.context['request'])
        # if not device_id:
        #     raise ValidationError(_('Device id required'))
        # is_exist_device = models.User.objects.filter(device_id=device_id)
        # if is_exist_device:
        #     raise ValidationError(_('This device already used'))
        # attrs['device_id'] = device_id

        return attrs

    def create(self, validated_data: dict) -> models.User:
        validated_data['email'] = validated_data['email'].lower()
        password_candidate = validated_data['password']

        user = models.User(**validated_data)
        user.set_password(password_candidate)
        try:
            user.save()
        except Exception:
            raise ValidationError(_('Registration error'))

        try:
            _send_verification_email(user_id=user.pk)
        except Exception as e:
            print(f'\033[91m {str(e)} \033[0m')

        return user

    class Meta:
        model = models.User
        fields = ('email', 'password', 'detail',)


class PhoneRegistrationSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    detail = serializers.CharField(
        read_only=True, default='success', required=False)

    def validate(self, attrs):
        password_candidate = self.context['request'].data['password']
        utils.is_valid_password(password_candidate)

        # IF NEED
        # device_id = utils.get_device_id_from_request(self.context['request'])
        # if not device_id:
        #     raise ValidationError(_('Device id required'))
        # is_exist_device = models.User.objects.filter(device_id=device_id)
        # if is_exist_device:
        #     raise ValidationError(_('This device already used'))
        # attrs['device_id'] = device_id

        return attrs

    def create(self, validated_data: dict) -> models.User:
        phone = validated_data['phone']
        if models.User.objects.filter(phone=phone).exists():
            raise ValidationError(_('Already registered'))

        user = models.User.objects.create(
            phone=phone,
        )
        user.set_password(validated_data['password'])
        user.save()
        # try:
        # client = SmsClient()
        # is_sent = client.send_sms_verification(user.phone)
        # if not is_sent:
        # raise ValidationError(_('Could not send verification sms'))
        # except Exception as e:
        # print(f'\033[91m {str(e)} \033[0m')

        return user

    class Meta:
        model = models.User
        fields = ('phone', 'password', 'detail',)


class LoginEmailSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs['email'] = attrs['email'].lower()
        return super().validate(attrs)


class LoginPhoneSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs['phone'] = attrs['phone']
        return super().validate(attrs)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ('name', 'surname', 'email', 'phone', 'avatar',
                  'is_email_verified', 'is_phone_verified', 'is_superuser')


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ('name', 'surname')


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ('avatar',)


# PASSWORD CHANGE SERIALIZERS
class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        write_only=True,
        allow_null=False,
        allow_blank=False
    )
    new_password = serializers.CharField(
        write_only=True,
        allow_blank=False,
        allow_null=False
    )

    def create(self, validated_data: dict) -> models.User:
        old_password = validated_data.get('old_password')
        new_password = validated_data.get('new_password')

        user = self.context.get('request').user

        if not user.check_password(old_password):
            raise ValidationError(_('Invalid old password'))

        user.set_password(new_password)
        user.save()
        return user

    class Meta:
        model = models.User
        fields = ('old_password', 'new_password')


# PASSWORD RESET SERIALIZERS BY EMAIL
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def create(self, validated_data):
        email_candidate = validated_data.get('email')

        user = models.User.objects.filter(email=email_candidate).first()
        if not user:
            raise ValidationError(_('User not found'))

        code = utils.generate_verification_code()
        print('code: ', code)
        utils.set_verification_code(
            code, enums.UserSecurityCode.RESET_PASSWORD, user.id)
        celery_app.send_task(
            'send_password_reset_request_email',
            kwargs={
                'user_id': user.id,
                'code': code
            }
        )
        return validated_data


class CheckPasswordResetCodeSerialiser(serializers.Serializer):
    email_candidate = serializers.EmailField(write_only=True)
    code_candidate = serializers.CharField(write_only=True)

    def create(self, validated_data):
        email_candidate = validated_data.get('email_candidate')
        code_candidate = validated_data.get('code_candidate')

        if not email_candidate or not code_candidate:
            raise ValidationError(_('Email or code cant be blank'))

        success, error = check_password_reset_code_exist(
            user_email=email_candidate, code=code_candidate
        )
        if error:
            raise ValidationError(_('Code is NOT valid'))
        return validated_data


class PasswordResetSubmitSerialiser(serializers.Serializer):
    code_candidate = serializers.CharField(write_only=True)
    password_candidate = serializers.CharField(write_only=True)

    def create(self, validated_data):
        code_candidate = validated_data.get('code_candidate')
        password_candidate = validated_data.get('password_candidate')

        if not code_candidate or not password_candidate:
            raise ValidationError(_('Not all fields are filled correctly'))

        is_valid = utils.is_valid_password(password_candidate)

        if is_valid != True:
            raise ValidationError(
                _('Password must contain at least 8 Characters: 1 lowercase or 1 uppercase, and 1 digit'))

        user_id = utils.get_verification_code(
            code_candidate, enums.UserSecurityCode.RESET_PASSWORD)
        if not user_id:
            raise ValidationError(_('Code doest exist'))

        user = models.User.objects.filter(id=user_id).first()
        if not user:
            raise exception.get(ValidationError, _('User does not exist'))

        if user.check_password(password_candidate):
            raise ValidationError(
                _('Old password cant be used as new password'))

        updated = False
        try:
            user.set_password(password_candidate)
            user.save()
            updated = True
        except Exception as e:
            raise ValidationError(_('Update password error'))

        if updated:
            utils.delete_used_code(
                code_candidate, enums.UserSecurityCode.RESET_PASSWORD)

        return Response({_('Password was successfully updated')}, status.HTTP_200_OK)


def check_password_reset_code_exist(user_email, code) -> Tuple[bool, Optional[str]]:
    user = models.User.objects.filter(email=user_email).first()

    if not user:
        raise ValidationError(_('User does not exist'))

    user_id_from_code = utils.get_verification_code(
        code, enums.UserSecurityCode.RESET_PASSWORD)

    if not (user_id_from_code) or (int(user_id_from_code) != user.id):
        return False, _('This code does not exist')

    return True, None


def _send_verification_email(user_id):
    code = utils.generate_verification_code()
    utils.set_verification_code(
        code, enums.UserSecurityCode.VERIFY_EMAIL, user_id)
    celery_app.send_task(
        'send_verify_email',
        kwargs={
            'user_id': user_id,
            'code': code
        }
    )


class EmailVerifyRequestSerialiser(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        email_candidate = validated_data.get('email')
        user = get_object_or_404(models.User, email=email_candidate)

        if user.is_email_verified:
            raise ValidationError(_('Email already verified'))
        else:
            try:
                _send_verification_email(user_id=user.id)
            except Exception as e:
                print(f'\033[91m {str(e)} \033[0m')

        return user


class EmailVerifySubmitSerialiser(serializers.Serializer):
    email = serializers.EmailField()
    code_candidate = serializers.CharField(write_only=True)

    def create(self, validated_data):
        email_candidate = validated_data.get('email')
        code_candidate = validated_data.get('code_candidate')

        if not email_candidate or not code_candidate:
            raise ValidationError(_('Not all fields are filled correctly'))

        is_valid_code = utils.compare_verification_code(
            code_candidate, enums.UserSecurityCode.VERIFY_EMAIL)
        if not is_valid_code:
            raise ValidationError(_('Wrong code'))

        user = models.User.objects.filter(email=email_candidate).first()

        if not user:
            raise ValidationError(_('User not found'))

        user.is_email_verified = True
        user.save()

        utils.delete_used_code(
            code_candidate, enums.UserSecurityCode.VERIFY_EMAIL)

        if user:
            return user
        return None


# PASSWORD FORGOT SERIALIZERS BY PHONE
# TODO: finish and continue
class PasswordForgotRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    detail = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    def validate(self, attrs):
        phone_candidate = attrs.get('phone')
        user = models.User.objects.filter(phone=phone_candidate).first()
        if not user:
            raise ValidationError(_('User with this phone not found'))
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        # try:
        #     client = SmsClient()
        #     is_sent = client.send_sms_verification(user.phone)
        #     if not is_sent:
        #         raise ValidationError(_('Could not send verification sms'))
        # except Exception as e:
        #     print(f'\033[91m {str(e)} \033[0m')

        return {'detail': 'Code was successfully send', 'status': status.HTTP_200_OK}


class PasswordForgotVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    code = serializers.CharField(write_only=True)
    detail = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    def validate(self, attrs):
        phone_candidate = attrs.get('phone')
        code_candidate = attrs.get('code')
        if not phone_candidate or not code_candidate:
            raise ValidationError(_('Not all fields are filled correctly'))

        # TODO:
        utils.is_valid_phone(phone_candidate)

        user = models.User.objects.filter(phone=phone_candidate).first()
        if not user:
            raise ValidationError(_('User not found'))

        attrs['user'] = user
        attrs['code'] = code_candidate
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        code = validated_data['code']

        # is_code_valid = SmsClient().check_sms_code(
        #     code=code,
        #     phone_number=user.phone
        # )

        # if not is_code_valid:
        #     raise ValidationError(_('Invalid code'))

        user.is_pwd_reset_allow = True
        user.save()

        return {'detail': 'Code is valid, user can set new password', 'status': status.HTTP_200_OK}


# class SocialSerializer(serializers.ModelSerializer):
#     OAUTH_HANDLER = None
#
#     oauth_token = serializers.CharField(write_only=True, required=True, allow_null=False, allow_blank=False)
#     access = serializers.SerializerMethodField()
#     refresh = serializers.SerializerMethodField()
#
#     class Meta:
#         model = models.User
#         fields = ('access', 'refresh', 'oauth_token')
#
#     def create(self, validated_data):
#         oauth_token = validated_data.get('oauth_token')
#         oauth_handler = self.OAUTH_HANDLER(oauth_token)
#         user = oauth_handler.get_user()
#
#         if user is None:
#             raise serializers.ValidationError('Could not fetch user from social authentication.')
#
#         return user
#
#     def get_access(self, obj: models.User) -> str:
#         refresh_token = RefreshToken.for_user(obj)
#         return str(refresh_token.access_token)
#
#     def get_refresh(self, obj: models.User) -> str:
#         refresh_token = RefreshToken.for_user(obj)
#         return str(refresh_token)
#
#
# class GoogleAuthSerializer(SocialSerializer):
#     OAUTH_HANDLER = social_oauth.GoogleUser
#
#
# class FacebookAuthSerializer(SocialSerializer):
#     OAUTH_HANDLER = social_oauth.FacebookUser
#
#
# class AppleAuthSerializer(SocialSerializer):
#     OAUTH_HANDLER = social_oauth.AppleUser
