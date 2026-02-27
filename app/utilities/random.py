import secrets
import string


def generate_secure_otp(length: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP."""
    # Use only digits
    allowed_characters = string.digits

    # Generate a random OTP using secrets.choice for each digit
    otp = ''.join(secrets.choice(allowed_characters) for _ in range(length))

    # Casting resulting value to int
    return otp
