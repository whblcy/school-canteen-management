"""
分类与供应商仓储
"""
from typing import Optional, List
from ..models import Category, Supplier, CategoryMapping, Ingredient
from .base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category
    ALLOWED_FIELDS = {"name", "description"}

    def get_all_ordered(self, order_field: str = "name", limit: int = 500) -> List[Category]:
        return list(Category.select().order_by(Category.name))

    def get_by_name(self, name: str) -> Optional[Category]:
        return Category.get_or_none(Category.name == name)

    def create(self, name: str, description: str = "") -> Category:
        return Category.create(name=name, description=description)


class SupplierRepository(BaseRepository[Supplier]):
    model = Supplier
    ALLOWED_FIELDS = {"name", "contact_person", "phone", "address", "email", "status"}

    def get_all_ordered(self, order_field: str = "name", limit: int = 500) -> List[Supplier]:
        return list(Supplier.select().order_by(Supplier.name))

    def get_active(self) -> List[Supplier]:
        return list(Supplier.select().where(Supplier.status == 1).order_by(Supplier.name))

    def get_by_name(self, name: str) -> Optional[Supplier]:
        return Supplier.get_or_none(Supplier.name == name)

    def create(self, name: str, contact_person: str = "", phone: str = "",
               address: str = "", email: str = "") -> Supplier:
        return Supplier.create(name=name, contact_person=contact_person,
                               phone=phone, address=address, email=email)


class CategoryMappingRepository(BaseRepository[CategoryMapping]):
    model = CategoryMapping
    ALLOWED_FIELDS = {"source_category", "target_category", "description"}

    def get_all_ordered(self, order_field: str = "source_category", limit: int = 500) -> List[CategoryMapping]:
        return list(
            CategoryMapping
            .select(CategoryMapping, Category)
            .join(Category, on=(CategoryMapping.target_category == Category.id))
            .order_by(CategoryMapping.source_category)
        )

    def get_by_source(self, source: str) -> Optional[CategoryMapping]:
        return CategoryMapping.get_or_none(CategoryMapping.source_category == source)

    def get_source_to_name_map(self) -> dict:
        """返回 {source_category: target_category_name} 映射"""
        mappings = (
            CategoryMapping
            .select(CategoryMapping, Category)
            .join(Category)
        )
        return {m.source_category: m.target_category.name for m in mappings}
