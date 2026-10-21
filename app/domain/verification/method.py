from enum import StrEnum


class VerificationMethod(StrEnum):
    """Ways a 21ID user can prove ownership of a School 21 account."""

    EMAIL_OTP = "email_otp"
    INVITE = "invite"
    MIGRATION_OTP = "migration_otp"
    # Temporary: owner-made link with a list of nicknames, no OTP
    MASS_INVITE = "mass_invite"
    # FACE_ID = "face_id" - add here together with its provider
