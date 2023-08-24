from rest_framework import generics
from twilio_sms import serializers


class CreateSmsView(generics.CreateAPIView):
    """
        Send verification code.

        Send verification code.
    """
    authentication_classes = []
    serializer_class = serializers.CreateSmsSerializer


class VerifySmsView(generics.CreateAPIView):
    """
        Verify code.

        After verification model of user will update param is_phone_verified.
    """
    authentication_classes = []
    serializer_class = serializers.VerifySmsSerializer
