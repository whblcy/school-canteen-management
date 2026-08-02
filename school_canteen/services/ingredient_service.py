"""
食材服务 - 食材 CRUD 与库存查询
"""
from typing import List, Optional
from ..data.models import Ingredient
from ..data.repositories.ingredient_repository import IngredientRepository
from ..data.repositories.catalog_repository import CategoryRepository, SupplierRepository
from ..core.exceptions import DuplicateError, NotFoundError, ValidationError
from ..core.session import Session
from ..utils.logging_config import get_logger

logger = get_logger()


class IngredientService:
    """食材服务"""

    def __init__(self, ingredient_repo: IngredientRepository,
                 category_repo: CategoryRepository,
                 supplier_repo: SupplierRepository,
                 log_repo=None):
        self.ingredient_repo = ingredient_repo
        self.category_repo = category_repo
        self.supplier_repo = supplier_repo
        self.log_repo = log_repo

    def get_all_ingredients(self) -> List[Ingredient]:
        return self.ingredient_repo.get_all_with_relations()

    def get_ingredient(self, id: int) -> Ingredient:
        ing = self.ingredient_repo.get_by_id_with_relations(id)
        if not ing:
            raise NotFoundError("食材", id)
        return ing

    def get_low_stock(self) -> List[Ingredient]:
        """获取低库存食材"""
        return self.ingredient_repo.get_low_stock()

    def create_ingredient(self, name: str, category_name: str = None,
                          unit: str = "个", specification: str = "",
                          safety_stock: float = 0, supplier_name: str = None) -> Ingredient:
        """创建食材，自动创建不存在的分类和供应商"""
        if not name or not name.strip():
            raise ValidationError("食材名称不能为空")
        if self.ingredient_repo.get_by_name(name.strip()):
            raise DuplicateError("食材", name)

        category_id = None
        if category_name:
            cat = self.category_repo.get_by_name(category_name.strip())
            if not cat:
                cat = self.category_repo.create(name=category_name.strip())
            category_id = cat.id

        supplier_id = None
        if supplier_name:
            sup = self.supplier_repo.get_by_name(supplier_name.strip())
            if not sup:
                sup = self.supplier_repo.create(name=supplier_name.strip())
            supplier_id = sup.id

        if safety_stock < 0:
            raise ValidationError("安全库存不能为负数")

        ing = self.ingredient_repo.create(
            name=name.strip(), category_id=category_id, unit=unit.strip(),
            specification=specification, safety_stock=safety_stock,
            supplier_id=supplier_id,
        )
        logger.info(f"创建食材: {name}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "新增食材", "ingredient", ing.id, name)
        return ing

    def update_ingredient(self, id: int, **kwargs) -> bool:
        ing = self.ingredient_repo.get_by_id(id)
        if not ing:
            raise NotFoundError("食材", id)
        if "name" in kwargs:
            existing = self.ingredient_repo.get_by_name(kwargs["name"])
            if existing and existing.id != id:
                raise DuplicateError("食材", kwargs["name"])
        if "safety_stock" in kwargs and (kwargs["safety_stock"] or 0) < 0:
            raise ValidationError("安全库存不能为负数")
        if "category_name" in kwargs:
            cat_name = kwargs.pop("category_name")
            if cat_name:
                cat = self.category_repo.get_by_name(cat_name)
                if not cat:
                    cat = self.category_repo.create(name=cat_name)
                kwargs["category"] = cat.id
        if "supplier_name" in kwargs:
            sup_name = kwargs.pop("supplier_name")
            if sup_name:
                sup = self.supplier_repo.get_by_name(sup_name)
                if not sup:
                    sup = self.supplier_repo.create(name=sup_name)
                kwargs["supplier"] = sup.id
        result = self.ingredient_repo.update(id, **kwargs)
        if result:
            logger.info(f"更新食材: id={id}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "更新食材", "ingredient", id)
        return result

    def delete_ingredient(self, id: int) -> bool:
        ing = self.ingredient_repo.get_by_id(id)
        if not ing:
            raise NotFoundError("食材", id)
        # 引用检查：有出入库记录或仍有库存的食材不允许删除，
        # 否则会触发外键错误或产生"幽灵库存"
        from ..data.models import StockIn, StockOut
        if StockIn.select().where(StockIn.ingredient == id).exists():
            raise ValidationError(
                f"食材「{ing.name}」存在入库记录，无法删除。\n"
                "请先在入库管理中删除相关记录。")
        if StockOut.select().where(StockOut.ingredient == id).exists():
            raise ValidationError(
                f"食材「{ing.name}」存在出库记录，无法删除。\n"
                "请先在出库管理中删除相关记录。")
        if ing.current_stock:
            raise ValidationError(
                f"食材「{ing.name}」当前库存为 {ing.current_stock}{ing.unit}，"
                "不为 0，无法删除。\n请先出库或盘点清零。")
        result = self.ingredient_repo.delete(id)
        if result:
            logger.info(f"删除食材: {ing.name}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "删除食材", "ingredient", id, ing.name)
        return result

    def batch_delete(self, ids: List[int]) -> int:
        """批量删除，返回成功数量"""
        count = 0
        for id in ids:
            try:
                if self.delete_ingredient(id):
                    count += 1
            except Exception as e:
                logger.warning(f"删除食材失败 id={id}: {e}")
        return count
