import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def compute_public_key(private_key_b64: str) -> str:
    pk = X25519PrivateKey.from_private_bytes(b64url_decode(private_key_b64))
    return b64url_encode(pk.public_key().public_bytes_raw())
