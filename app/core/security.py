from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
from config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """Password hashing utilities"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)


class JWTHandler:
    """JWT token handling"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None


class APIKeyEncryption:
    """AES-256 encryption for API keys"""

    def __init__(self):
        # Use the encryption key from settings
        # Ensure it's exactly 32 bytes for AES-256
        key = settings.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0')
        self.cipher = Fernet(base64.urlsafe_b64encode(key))

    def encrypt(self, plain_text: str) -> str:
        """Encrypt API key using AES-256"""
        if not plain_text:
            return None
        encrypted = self.cipher.encrypt(plain_text.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt API key"""
        if not encrypted_text:
            return None
        try:
            decrypted = self.cipher.decrypt(encrypted_text.encode())
            return decrypted.decode()
        except Exception:
            return None


class APIKeyManager:
    """Manager for encrypting and decrypting Binance API keys"""

    def __init__(self):
        self.encryption = APIKeyEncryption()

    def encrypt_api_credentials(self, api_key: str, api_secret: str) -> tuple:
        """Encrypt Binance API credentials"""
        encrypted_key = self.encryption.encrypt(api_key)
        encrypted_secret = self.encryption.encrypt(api_secret)
        return encrypted_key, encrypted_secret

    def decrypt_api_credentials(self, encrypted_key: str, encrypted_secret: str) -> tuple:
        """Decrypt Binance API credentials"""
        api_key = self.encryption.decrypt(encrypted_key)
        api_secret = self.encryption.decrypt(encrypted_secret)
        return api_key, api_secret


# Global instances
password_hasher = PasswordHasher()
jwt_handler = JWTHandler()
api_key_manager = APIKeyManager()