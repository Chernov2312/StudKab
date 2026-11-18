from hashlib import sha256
from secrets import token_urlsafe

from pwdlib import PasswordHash

passwords = PasswordHash.recommended()
dummy_hash = passwords.hash(token_urlsafe(32))


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()
