"""
领域异常体系 - 用语义化异常替代返回值判断
所有异常都携带足够的上下文信息，便于 UI 层展示和日志记录
"""


class AppError(Exception):
    """应用异常基类"""


class ValidationError(AppError):
    """输入校验失败（如数量为负、必填项为空）"""


class NotFoundError(AppError):
    """资源不存在"""
    def __init__(self, resource: str, id):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource}不存在: id={id}")


class BusinessRuleError(AppError):
    """业务规则违反（如库存不足、食材已过期）"""


class InsufficientStockError(BusinessRuleError):
    """库存不足"""
    def __init__(self, ingredient: str, current: float, requested: float):
        self.ingredient = ingredient
        self.current = current
        self.requested = requested
        super().__init__(f"库存不足，当前库存: {current}，请求出库: {requested}")


class ExpiredIngredientError(BusinessRuleError):
    """食材全部批次已过期，禁止出库（食品安全管控）"""
    def __init__(self, ingredient: str):
        self.ingredient = ingredient
        super().__init__(f"该食材所有入库批次已过期，禁止出库（食品安全管控）")


class DuplicateError(AppError):
    """唯一约束冲突（如重复的食材名称）"""
    def __init__(self, resource: str, name: str):
        self.resource = resource
        self.name = name
        super().__init__(f"{resource}已存在: {name}")


class AuthenticationError(AppError):
    """认证失败"""


class AuthorizationError(AppError):
    """权限不足（如非管理员执行用户管理操作、越权伪造时间等）"""


class DatabaseError(AppError):
    """数据库操作异常"""


class ReportTemplateError(AppError):
    """报表模板缺失或格式错误"""
