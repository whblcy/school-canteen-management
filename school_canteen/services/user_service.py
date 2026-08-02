# -*- coding: utf-8 -*-
"""
用户服务 - 用户管理（创建、列表、修改角色/状态、重置密码、删除）

仅系统管理员可调用本服务（UI 层已限制入口，且服务层 _require_admin 兜底）。
管理员账号受保护：不可被禁用、不可被修改角色、不可被删除。
"""
from typing import List, Optional

from ..data.models import User
from ..data.repositories.user_repository import UserRepository
from ..utils.security import hash_password
from ..core.exceptions import ValidationError, DuplicateError, AuthorizationError
from ..core.roles import VALID_ROLES, ROLE_ADMIN
from ..core.session import Session
from ..utils.logging_config import get_logger

logger = get_logger()


class UserService:
    """用户管理服务"""

    def __init__(self, user_repo: UserRepository, log_repo=None):
        self.user_repo = user_repo
        self.log_repo = log_repo

    def _require_admin(self):
        """仅系统管理员可执行用户管理操作"""
        if not Session.can_manage_users:
            raise AuthorizationError("仅系统管理员可进行用户管理操作")

    def get_all(self) -> List[User]:
        return self.user_repo.get_all_ordered()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

    def create_user(self, username: str, password: str,
                    real_name: str = "", role: str = "user",
                    status: int = 1) -> User:
        """创建用户"""
        self._require_admin()
        username = (username or "").strip()
        if not username:
            raise ValidationError("用户名不能为空")
        if len(password) < 6:
            raise ValidationError("密码长度不能少于6位")
        if self.user_repo.get_by_username(username):
            raise DuplicateError("用户", username)
        if role not in VALID_ROLES:
            raise ValidationError(f"未知角色: {role}")

        password_hash, salt = hash_password(password)
        user = self.user_repo.create(
            username=username, password_hash=password_hash, salt=salt,
            real_name=real_name, role=role, status=status,
        )
        logger.info(f"创建用户: {username} (role={role})")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "新增用户", "user", user.id, username)
        return user

    def update_role(self, user_id: int, role: str) -> bool:
        """修改用户角色（管理员角色不可被更改）"""
        self._require_admin()
        if role not in VALID_ROLES:
            raise ValidationError(f"未知角色: {role}")
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        if user.role == ROLE_ADMIN and role != ROLE_ADMIN:
            raise ValidationError("不能修改管理员的角色")
        return self.user_repo.update(user_id, role=role)

    def update_status(self, user_id: int, status: int) -> bool:
        """启用/禁用用户（管理员不可被禁用）"""
        self._require_admin()
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        if user.role == ROLE_ADMIN and status != 1:
            raise ValidationError("不能禁用管理员")
        return self.user_repo.update(user_id, status=status)

    def reset_password(self, user_id: int, new_password: str) -> bool:
        """重置用户密码"""
        self._require_admin()
        if len(new_password) < 6:
            raise ValidationError("新密码长度不能少于6位")
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        password_hash, salt = hash_password(new_password)
        return self.user_repo.update(
            user_id, password_hash=password_hash, salt=salt)

    def delete_user(self, user_id: int) -> bool:
        """删除用户（管理员不可被删除）"""
        self._require_admin()
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        if user.role == ROLE_ADMIN:
            raise ValidationError("不能删除管理员")
        return self.user_repo.delete(user_id)
