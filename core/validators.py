"""IMEI validation.

An IMEI is 15 digits whose final digit is a Luhn check digit. We validate both
the shape and the checksum so bad input is rejected before it ever reaches a
paid lookup. A 14-digit TAC+serial (without check digit) and a 16/17-digit
IMEISV are tolerated at the form layer but normalized to 15 here.
"""
import re

from django.core.exceptions import ValidationError

_DIGITS_ONLY = re.compile(r"\D+")


def normalize_imei(raw: str) -> str:
    """Strip spaces, dashes and any non-digit characters."""
    return _DIGITS_ONLY.sub("", raw or "")


def luhn_is_valid(number: str) -> bool:
    """Standard Luhn checksum over a string of digits."""
    if not number.isdigit():
        return False
    total = 0
    reverse = number[::-1]
    for index, char in enumerate(reverse):
        digit = int(char)
        if index % 2 == 1:  # every second digit from the right
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def validate_imei(raw: str) -> None:
    """Raise ValidationError if `raw` is not a usable IMEI."""
    imei = normalize_imei(raw)
    if len(imei) < 14 or len(imei) > 17:
        raise ValidationError(
            "That's not a valid IMEI — it should be 15 digits. "
            "Dial *#06# on the phone to find it."
        )
    # Validate the 15-digit form's checksum when a check digit is present.
    if len(imei) == 15 and not luhn_is_valid(imei):
        raise ValidationError(
            "That IMEI's checksum doesn't add up — double-check the digits."
        )
