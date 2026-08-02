"""
全局登录会话（单例）

保存当前已登录用户，供服务层写操作日志、视图预填操作员时引用。
刻意不依赖任何模型/服务，避免循环导入。
"""
from typing import Optional

from .roles import (
    can_set_custom_time, can_bypass_expiry, can_manage_users, role_label
)


class _Session:
    """进程内登录会话，记录当前已登录用户"""

    def __init__(self):
        self._user = None

    @property
    def current_user(self):
        """当前登录用户对象（peewee Model 实例），未登录为 None"""
        return self._user

    @current_user.setter
    def current_user(self, value):
        self._user = value

    @property
    def user_id(self) -> Optional[int]:
        """当前用户主键；未登录时为 None（操作日志可空）"""
        return self._user.id if self._user is not None else None

    @property
    def role(self) -> str:
        """当前用户角色；未登录时为空串"""
        if self._user is None:
            return ""
        return getattr(self._user, "role", "")

    @property
    def role_label(self) -> str:
        """当前用户角色的中文显示名"""
        return role_label(self.role)

    @property
    def can_set_custom_time(self) -> bool:
        """当前用户是否可自定义出入库时间"""
        return can_set_custom_time(self.role)

    @property
    def can_bypass_expiry(self) -> bool:
        """当前用户出库时是否可绕过保质期约束"""
        return can_bypass_expiry(self.role)

    @property
    def can_manage_users(self) -> bool:
        """当前用户是否可进入用户管理（仅管理员）"""
        return can_manage_users(self.role)

    @property
    def display_name(self) -> str:
        """当前用户展示名：优先 real_name，回退 username；未登录为空串"""
        if self._user is None:
            return ""
        name = getattr(self._user, "real_name", "") or ""
        if name:
            return name
        return getattr(self._user, "username", "")


# 全局唯一会话实例
Session = _Session()
