"""
分类、供应商、类别映射服务
"""
from typing import List, Optional
from ..data.models import Category, Supplier, CategoryMapping
from ..data.repositories.catalog_repository import (
    CategoryRepository, SupplierRepository, CategoryMappingRepository
)
from ..core.exceptions import DuplicateError, NotFoundError, ValidationError
from ..core.session import Session
from ..utils.logging_config import get_logger

logger = get_logger()


class CategoryService:
    """分类服务"""

    def __init__(self, category_repo: CategoryRepository, log_repo=None):
        self.category_repo = category_repo
        self.log_repo = log_repo

    def get_all(self) -> List[Category]:
        return self.category_repo.get_all_ordered()

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.category_repo.get_by_name(name)

    def create(self, name: str, description: str = "") -> Category:
        if not name or not name.strip():
            raise ValidationError("分类名称不能为空")
        if self.category_repo.get_by_name(name.strip()):
            raise DuplicateError("分类", name)
        cat = self.category_repo.create(name=name.strip(), description=description)
        logger.info(f"创建分类: {name}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "新增分类", "category", cat.id, name)
        return cat

    def update(self, id: int, name: str = None, description: str = None) -> bool:
        cat = self.category_repo.get_by_id(id)
        if not cat:
            raise NotFoundError("分类", id)
        if name and name != cat.name:
            existing = self.category_repo.get_by_name(name)
            if existing and existing.id != id:
                raise DuplicateError("分类", name)
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        result = self.category_repo.update(id, **kwargs)
        if result:
            logger.info(f"更新分类: id={id}")
        return result

    def delete(self, id: int) -> bool:
        cat = self.category_repo.get_by_id(id)
        if not cat:
            raise NotFoundError("分类", id)
        # 引用检查：分类下存在食材时不允许删除
        from ..data.models import Ingredient
        if Ingredient.select().where(Ingredient.category == id).exists():
            raise ValidationError(
                f"分类「{cat.name}」下存在食材，无法删除。\n"
                "请先将该分类下的食材移出或删除。")
        result = self.category_repo.delete(id)
        if result:
            logger.info(f"删除分类: {cat.name}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "删除分类", "category", id, cat.name)
        return result


class SupplierService:
    """供应商服务"""

    def __init__(self, supplier_repo: SupplierRepository, log_repo=None):
        self.supplier_repo = supplier_repo
        self.log_repo = log_repo

    def get_all(self) -> List[Supplier]:
        return self.supplier_repo.get_all_ordered()

    def get_active(self) -> List[Supplier]:
        return self.supplier_repo.get_active()

    def get_by_name(self, name: str) -> Optional[Supplier]:
        return self.supplier_repo.get_by_name(name)

    def create(self, name: str, contact_person: str = "", phone: str = "",
               address: str = "", email: str = "") -> Supplier:
        if not name or not name.strip():
            raise ValidationError("供应商名称不能为空")
        if self.supplier_repo.get_by_name(name.strip()):
            raise DuplicateError("供应商", name)
        sup = self.supplier_repo.create(name=name.strip(), contact_person=contact_person,
                                        phone=phone, address=address, email=email)
        logger.info(f"创建供应商: {name}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "新增供应商", "supplier", sup.id, name)
        return sup

    def update(self, id: int, **kwargs) -> bool:
        sup = self.supplier_repo.get_by_id(id)
        if not sup:
            raise NotFoundError("供应商", id)
        if "name" in kwargs and kwargs["name"] != sup.name:
            existing = self.supplier_repo.get_by_name(kwargs["name"])
            if existing and existing.id != id:
                raise DuplicateError("供应商", kwargs["name"])
        result = self.supplier_repo.update(id, **kwargs)
        if result:
            logger.info(f"更新供应商: id={id}")
        return result

    def delete(self, id: int) -> bool:
        sup = self.supplier_repo.get_by_id(id)
        if not sup:
            raise NotFoundError("供应商", id)
        # 引用检查：供应商被食材或入库记录引用时不允许删除
        from ..data.models import Ingredient, StockIn
        if Ingredient.select().where(Ingredient.supplier == id).exists():
            raise ValidationError(
                f"供应商「{sup.name}」被食材引用，无法删除。\n"
                "请先将该供应商下的食材移出或删除。")
        if StockIn.select().where(StockIn.supplier == id).exists():
            raise ValidationError(
                f"供应商「{sup.name}」存在入库记录，无法删除。\n"
                "请先删除相关入库记录。")
        result = self.supplier_repo.delete(id)
        if result:
            logger.info(f"删除供应商: {sup.name}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "删除供应商", "supplier", id, sup.name)
        return result


class CategoryMappingService:
    """类别映射服务"""

    def __init__(self, mapping_repo: CategoryMappingRepository,
                 category_repo: CategoryRepository, log_repo=None):
        self.mapping_repo = mapping_repo
        self.category_repo = category_repo
        self.log_repo = log_repo

    def get_all(self) -> List[CategoryMapping]:
        return self.mapping_repo.get_all_ordered()

    def get_source_to_name_map(self) -> dict:
        """返回 {source: target_name} 映射"""
        return self.mapping_repo.get_source_to_name_map()

    def create(self, source_category: str, target_category_id: int,
               description: str = "") -> CategoryMapping:
        if not source_category or not source_category.strip():
            raise ValidationError("源类别名称不能为空")
        if self.mapping_repo.get_by_source(source_category.strip()):
            raise DuplicateError("类别映射", source_category)
        cat = self.category_repo.get_by_id(target_category_id)
        if not cat:
            raise NotFoundError("目标分类", target_category_id)
        mapping = self.mapping_repo.create(
            source_category=source_category.strip(),
            target_category=target_category_id,
            description=description,
        )
        logger.info(f"创建类别映射: {source_category} → {cat.name}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "新增类别映射", "category_mapping", mapping.id)
        return mapping

    def update(self, id: int, source_category: str = None,
               target_category_id: int = None, description: str = None) -> bool:
        mapping = self.mapping_repo.get_by_id(id)
        if not mapping:
            raise NotFoundError("类别映射", id)
        kwargs = {}
        if source_category is not None:
            kwargs["source_category"] = source_category
        if target_category_id is not None:
            cat = self.category_repo.get_by_id(target_category_id)
            if not cat:
                raise NotFoundError("目标分类", target_category_id)
            kwargs["target_category"] = target_category_id
        if description is not None:
            kwargs["description"] = description
        result = self.mapping_repo.update(id, **kwargs)
        if result:
            logger.info(f"更新类别映射: id={id}")
        return result

    def delete(self, id: int) -> bool:
        mapping = self.mapping_repo.get_by_id(id)
        if not mapping:
            raise NotFoundError("类别映射", id)
        result = self.mapping_repo.delete(id)
        if result:
            logger.info(f"删除类别映射: {mapping.source_category}")
        return result
