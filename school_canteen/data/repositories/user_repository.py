"""
用户仓储 - 认证与用户管理
"""
from typing import Optional, List
from ..models import User
from .base import BaseRepository
from ...utils.security import verify_password


class UserRepository(BaseRepository[User]):
    model = User
    ALLOWED_FIELDS = {"password_hash", "salt", "real_name", "role", "status"}

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """认证用户，验证密码"""
        user = User.get_or_none(
            (User.username == username) & (User.status == 1)
        )
        if not user:
            return None
        if verify_password(password, user.salt, user.password_hash):
            return user
        return None

    def get_by_username(self, username: str) -> Optional[User]:
        return User.get_or_none(User.username == username)

    def get_all_ordered(self, order_field: str = "username", limit: int = 500) -> List[User]:
        return list(User.select().order_by(User.username))

    def create(self, username: str, password_hash: str, salt: str,
               real_name: str = "", role: str = "user",
               status: int = 1) -> User:
        return User.create(
            username=username, password_hash=password_hash, salt=salt,
            real_name=real_name, role=role, status=status,
        )

    def delete(self, id: int) -> bool:
        """禁止删除 admin 角色"""
        user = self.get_by_id(id)
        if user and user.role == "admin":
            return False
        return super().delete(id)
