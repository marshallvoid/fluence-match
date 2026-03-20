from cryptography.fernet import Fernet


class EncryptComputer:
    def __init__(self, secret_key: str) -> None:
        self._fernet = Fernet(secret_key)

    def encrypt(self, value: bytes) -> bytes:
        return self._fernet.encrypt(value)

    def decrypt(self, value: bytes) -> bytes:
        return self._fernet.decrypt(value)
