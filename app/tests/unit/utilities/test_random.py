import string

from app.utilities import random

import pytest


@pytest.mark.parametrize("length", [4, 6, 10])
def test_secure_otp_digits_only(length):
    for _ in range(50):
        otp = random.generate_secure_otp(length)
        assert len(otp) == length and otp.isdigit()


def test_secure_otp_is_random():
    assert len({random.generate_secure_otp() for _ in range(50)}) > 40


def test_migration_otp_charset_and_uppercase():
    allowed = set(string.digits + string.ascii_uppercase)
    for _ in range(100):
        otp = random.generate_migration_otp()
        assert len(otp) == 8
        assert set(otp) <= allowed
        assert sum(c.isupper() for c in otp) >= 3


def test_migration_otp_custom_params():
    otp = random.generate_migration_otp(length=4, min_uppercase=4)
    assert len(otp) == 4 and otp.isupper() and otp.isalpha()
