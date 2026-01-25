"""Two-factor authentication utilities."""

import secrets
from urllib.parse import quote

import pyotp


def generate_totp_secret() -> str:
    """Generate a new TOTP secret."""
    return pyotp.random_base32()


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_qr_code_url(secret: str, email: str, issuer: str = "OmniSupport") -> str:
    """Generate QR code URL for authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate backup codes for 2FA recovery."""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric codes
        code = secrets.token_hex(4).upper()
        # Format as XXXX-XXXX for readability
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash a backup code for storage."""
    import hashlib

    # Remove formatting
    clean_code = code.replace("-", "").upper()
    return hashlib.sha256(clean_code.encode()).hexdigest()


def verify_backup_code(code: str, hashed_codes: list[str]) -> tuple[bool, str | None]:
    """
    Verify a backup code against stored hashes.
    Returns (is_valid, used_hash) tuple.
    """
    hashed = hash_backup_code(code)
    if hashed in hashed_codes:
        return True, hashed
    return False, None
