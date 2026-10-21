import secrets
import string


def generate_secure_otp(length: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP."""
    # Use only digits
    allowed_characters = string.digits

    # Generate a random OTP using secrets.choice for each digit
    otp = "".join(secrets.choice(allowed_characters) for _ in range(length))

    # Casting resulting value to int
    return otp


def generate_migration_otp(length: int = 8, min_uppercase: int = 3) -> str:
    """Generates a cryptographically secure alphanumeric OTP for account migration."""
    allowed_characters = string.digits + string.ascii_uppercase

    while True:
        otp = "".join(secrets.choice(allowed_characters) for _ in range(length))
        if sum(1 for c in otp if c.isupper()) >= min_uppercase:
            return otp
