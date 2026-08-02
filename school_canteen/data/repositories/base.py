"""
仓储基类 - 提供通用 CRUD 操作
子类指定模型类，即可继承全部基础操作
"""
from typing import TypeVar, Generic, Type, Optional, List
from peewee import Model, DoesNotExist

M = TypeVar("M", bound=Model)


class BaseRepository(Generic[M]):
    """泛型仓储基类"""
    model: Type[M] = None

    def __init__(self, model: Type[M] = None):
        if model is not None:
            self.model = model

    def get_by_id(self, id: int) -> Optional[M]:
        try:
            return self.model.get_by_id(id)
        except DoesNotExist:
            return None

    def get_all(self, limit: int = 500) -> List[M]:
        return list(self.model.select().limit(limit))

    def get_all_ordered(self, order_field: str = "id", limit: int = 500) -> List[M]:
        field = getattr(self.model, order_field, None)
        query = self.model.select()
        if field is not None:
            query = query.order_by(field)
        return list(query.limit(limit))

    def count(self) -> int:
        return self.model.select().count()

    def create(self, **kwargs) -> M:
        return self.model.create(**kwargs)

    def update(self, id: int, **kwargs) -> bool:
        # 字段白名单防注入（子类可覆盖 ALLOWED_FIELDS）
        allowed = getattr(self, "ALLOWED_FIELDS", None)
        if allowed is not None:
            kwargs = {k: v for k, v in kwargs.items() if k in allowed}
        if not kwargs:
            return False
        rows = self.model.update(**kwargs).where(self.model.id == id).execute()
        return rows > 0

    def delete(self, id: int) -> bool:
        rows = self.model.delete().where(self.model.id == id).execute()
        return rows > 0

    def exists(self, id: int) -> bool:
        return self.model.select().where(self.model.id == id).exists()
