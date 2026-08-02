"""
认证服务 - 登录、密码管理
"""
from typing import Optional
from ..data.models import User
from ..data.repositories.user_repository import UserRepository
from ..utils.security import hash_password, verify_password
from ..core.exceptions import AuthenticationError, ValidationError
from ..core.session import Session
from ..utils.logging_config import get_logger

logger = get_logger()


class AuthService:
    """认证服务"""

    def __init__(self, user_repo: UserRepository, log_repo=None):
        self.user_repo = user_repo
        self.log_repo = log_repo
        self._current_user: Optional[User] = None

    def login(self, username: str, password: str) -> Optional[User]:
        """用户登录"""
        user = self.user_repo.authenticate(username, password)
        if user is None:
            logger.warning(f"登录失败: username={username}")
            raise AuthenticationError("用户名或密码错误")
        self._current_user = user
        Session.current_user = user
        logger.info(f"用户登录: {username}")
        if self.log_repo:
            self.log_repo.add(user.id, "登录")
        return user

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def logout(self):
        if self._current_user:
            logger.info(f"用户登出: {self._current_user.username}")
            if self.log_repo:
                self.log_repo.add(self._current_user.id, "登出")
            self._current_user = None
            Session.current_user = None

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        if not verify_password(old_password, user.salt, user.password_hash):
            raise ValidationError("原密码错误")
        if len(new_password) < 6:
            raise ValidationError("新密码长度不能少于6位")
        password_hash, salt = hash_password(new_password)
        self.user_repo.update(user_id, password_hash=password_hash, salt=salt)
        logger.info(f"密码已修改: user_id={user_id}")
        if self.log_repo:
            self.log_repo.add(user_id, "修改密码")
        return True
