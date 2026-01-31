import pyotp
import time
class TOTPGenerator:
    def __init__(self, secret: str):
        self.totp = pyotp.TOTP(secret)

    def now(self) -> str:
        return self.totp.now()

    def remaining(self) -> int:
        return 30 - (int(time.time()) % 30)
        