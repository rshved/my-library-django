from enum import Enum


class UserSecurityCode(str, Enum):
    REFRESH_PASSWORD = "REFRESH_PASSWORD"
    VERIFY_EMAIL = "VERIFY_EMAIL"
    RESET_PASSWORD = "RESET_PASSWORD"
