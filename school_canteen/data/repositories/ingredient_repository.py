"""
食材仓储 - 含库存操作
"""
from typing import Optional, List
from peewee import fn, JOIN
from ..models import Ingredient, Category, Supplier
from .base import BaseRepository


class IngredientRepository(BaseRepository[Ingredient]):
    model = Ingredient
    ALLOWED_FIELDS = {
        "name", "category", "unit", "specification",
        "safety_stock", "current_stock", "supplier", "status",
    }

    def get_all_with_relations(self) -> List[Ingredient]:
        """获取全部食材，带分类名与供应商名"""
        return list(
            Ingredient
            .select(Ingredient, Category, Supplier)
            .join(Category, JOIN.LEFT_OUTER, on=(Ingredient.category == Category.id))
            .switch(Ingredient)
            .join(Supplier, JOIN.LEFT_OUTER, on=(Ingredient.supplier == Supplier.id))
            .order_by(Ingredient.name)
        )

    def get_by_id_with_relations(self, id: int) -> Optional[Ingredient]:
        return (
            Ingredient
            .select(Ingredient, Category, Supplier)
            .join(Category, JOIN.LEFT_OUTER, on=(Ingredient.category == Category.id))
            .switch(Ingredient)
            .join(Supplier, JOIN.LEFT_OUTER, on=(Ingredient.supplier == Supplier.id))
            .where(Ingredient.id == id)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Ingredient]:
        return Ingredient.get_or_none(Ingredient.name == name)

    def get_low_stock(self) -> List[Ingredient]:
        """低库存食材：当前库存 <= 安全库存"""
        return list(
            Ingredient
            .select(Ingredient, Category, Supplier)
            .join(Category, JOIN.LEFT_OUTER, on=(Ingredient.category == Category.id))
            .switch(Ingredient)
            .join(Supplier, JOIN.LEFT_OUTER, on=(Ingredient.supplier == Supplier.id))
            .where(
                (Ingredient.current_stock <= Ingredient.safety_stock)
                & (Ingredient.status == 1)
            )
            .order_by(Ingredient.name)
        )

    def update_stock(self, id: int, delta: float) -> bool:
        """增减库存（delta 正为入库，负为出库）"""
        rows = (
            Ingredient
            .update(current_stock=Ingredient.current_stock + delta)
            .where(Ingredient.id == id)
            .execute()
        )
        return rows > 0

    def set_stock(self, id: int, stock: float) -> bool:
        """直接设置库存值（盘点校正用）"""
        rows = (
            Ingredient
            .update(current_stock=stock)
            .where(Ingredient.id == id)
            .execute()
        )
        return rows > 0

    def get_stock(self, id: int) -> float:
        ing = self.get_by_id(id)
        return ing.current_stock if ing else 0

    def create(self, name: str, category_id: int = None, unit: str = "",
               specification: str = "", safety_stock: float = 0,
               supplier_id: int = None) -> Ingredient:
        kwargs = dict(name=name, unit=unit, specification=specification,
                      safety_stock=safety_stock)
        if category_id is not None:
            kwargs["category"] = category_id
        if supplier_id is not None:
            kwargs["supplier"] = supplier_id
        return Ingredient.create(**kwargs)
