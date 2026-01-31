from cryptography.fernet import Fernet
from app.core.config import settings
import base64

def get_fernet():
    try:
        return Fernet(settings.TOKEN_ENCRYPTION_KEY)
    except ValueError:
        # If the key is not valid base64 (e.g. just a random string), we can't easily auto-fix it 
        # without risking compatibility. But the user prompt said "Production-grade".
        # Let's assume the user provides a generated valid key. 
        # If not, this will raise, which is good (fail securely).
        return Fernet(settings.TOKEN_ENCRYPTION_KEY)

def encrypt_data(plain_text: str) -> str:
    """Encrypts plain text string to encrypted token string"""
    if not plain_text:
        return ""
    f = get_fernet()
    encrypted = f.encrypt(plain_text.encode())
    return encrypted.decode()

def decrypt_data(cipher_text: str) -> str:
    """Decrypts encrypted token string to plain text string"""
    if not cipher_text:
        return ""
    f = get_fernet()
    decrypted = f.decrypt(cipher_text.encode())
    return decrypted.decode()