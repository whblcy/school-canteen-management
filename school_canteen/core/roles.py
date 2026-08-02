"""
角色定义与权限能力

系统角色:
- admin  : 系统管理员（拥有全部权限，含用户管理、自定义出入库时间、绕过保质期约束）
- manager: 库存主管（可自定义出入库时间、不受保质期约束，但无用户管理权限）
- user   : 普通操作员（遵循标准食品安全约束）

新增角色说明（库存主管 manager）:
食堂实际运营中，常常需要补录历史出入库数据（如系统未及时录入），
或处理临期/特殊调拨。标准食品安全规则会拦截"全部批次已过期"食材出库，
并强制出入库时间为当前时刻。库存主管角色被授权放宽这两处约束，
以便合法地回溯录入与特殊出库，同时操作日志仍会记录操作人，保证可追溯。
"""

ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_USER = "user"

ROLE_LABELS = {
    ROLE_ADMIN: "系统管理员",
    ROLE_MANAGER: "库存主管",
    ROLE_USER: "普通操作员",
}

# 合法角色集合
VALID_ROLES = set(ROLE_LABELS.keys())

# 可自定义出入库时间、可绕过保质期约束的特权角色
PRIVILEGED_ROLES = {ROLE_ADMIN, ROLE_MANAGER}

# 可进入"用户管理"页面的角色（仅管理员）
USER_MANAGEMENT_ROLES = {ROLE_ADMIN}


def can_set_custom_time(role: str) -> bool:
    """该角色是否可自定义出入库时间（用于回溯录入历史数据）"""
    return role in PRIVILEGED_ROLES


def can_bypass_expiry(role: str) -> bool:
    """该角色出库时是否可绕过'全部批次已过期'的食品安全拦截"""
    return role in PRIVILEGED_ROLES


def can_manage_users(role: str) -> bool:
    """该角色是否可进入用户管理页面"""
    return role in USER_MANAGEMENT_ROLES


def role_label(role: str) -> str:
    """返回角色的中文显示名，未知角色原样返回"""
    return ROLE_LABELS.get(role, role)
