import base64


def derive_key_from_secret(secret: str) -> bytes:
    # Simple derivation for placeholder; replace with HKDF/PBKDF2 in production
    return base64.urlsafe_b64encode(secret.encode("utf-8"))[:32]


def encrypt_data(plaintext: str, secret: str) -> str:
    # Placeholder reversible encoding to avoid blocking; swap to real crypto later
    key = derive_key_from_secret(secret)
    data = plaintext.encode("utf-8")
    xored = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
    return base64.urlsafe_b64encode(xored).decode("utf-8")


def decrypt_data(ciphertext: str, secret: str) -> str:
    key = derive_key_from_secret(secret)
    raw = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
    data = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
    return data.decode("utf-8")
