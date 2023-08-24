from twilio.rest import Client
from twilio.rest.verify.v2.service import ServiceContext

import settings
# from twilio_sms import enums as sms_enums


class SmsClient:
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

    def _get_service(self) -> ServiceContext:
        return self.client.verify.services(settings.TWILIO_SERVICE_UID)

    def send_sms_verification(self, phone_number: str) -> bool:
        service = self._get_service()
        try:
            response = service.verifications.create(
                to=phone_number,
                channel="sms"
            )
        except Exception:
            return False

        # return response.status in sms_enums.VerificationSmsStatus.ok_statuses()

    def check_sms_code(self, phone_number: str, code: str) -> bool:
        service = self._get_service()
        try:
            response = service.verification_checks.create(
                code=code,
                to=phone_number
            )
        except Exception:
            return False

        # return response.status == sms_enums.VerificationSmsStatus.APPROVED
