"""
安全工具 - 密码哈希与验证
PBKDF2-HMAC-SHA256 + 随机盐值，兼容旧版 SHA256
"""
import hashlib
import secrets
from typing import Tuple
from ..config import get_config


def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """密码哈希: PBKDF2 + 盐值"""
    cfg = get_config()
    if salt is None:
        salt = secrets.token_hex(cfg.security.salt_length)
    password_hash = hashlib.pbkdf2_hmac(
        cfg.security.hash_algorithm,
        password.encode(),
        salt.encode(),
        cfg.security.pbkdf2_iterations,
    ).hex()
    return password_hash, salt


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """验证密码，兼容旧版 SHA256"""
    # 先尝试 PBKDF2
    cfg = get_config()
    new_hash = hashlib.pbkdf2_hmac(
        cfg.security.hash_algorithm,
        password.encode(),
        salt.encode(),
        cfg.security.pbkdf2_iterations,
    ).hex()
    if new_hash == password_hash:
        return True
    # 兼容旧版 SHA256
    old_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    return old_hash == password_hash
