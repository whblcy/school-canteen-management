"""
查验记录与查验人员仓储
"""
from typing import Optional, List
from peewee import fn
from ..models import InspectionRecord, Inspector, StockIn, Ingredient
from .base import BaseRepository


class InspectionRecordRepository(BaseRepository[InspectionRecord]):
    model = InspectionRecord
    ALLOWED_FIELDS = {
        "stock_in", "ingredient", "quantity", "unit", "production_date",
        "shelf_life", "supplier_name", "supplier_address", "supplier_phone",
        "batch_number", "inspection_result", "inspector", "inspection_date",
        "certificate_no", "remark",
    }

    def get_all_with_ingredient(self, limit: int = 100) -> List[InspectionRecord]:
        return list(
            InspectionRecord
            .select(InspectionRecord, Ingredient)
            .join(Ingredient)
            .order_by(InspectionRecord.created_at.desc())
            .limit(limit)
        )

    def get_by_stock_in_id(self, stock_in_id: int) -> Optional[InspectionRecord]:
        return InspectionRecord.get_or_none(InspectionRecord.stock_in == stock_in_id)

    def get_by_date(self, date_str: str) -> List[InspectionRecord]:
        return list(
            InspectionRecord
            .select(InspectionRecord, Ingredient)
            .join(Ingredient)
            .where(InspectionRecord.inspection_date == date_str)
            .order_by(InspectionRecord.created_at.desc())
        )

    def get_by_date_range(self, date_from: str, date_to: str) -> List[InspectionRecord]:
        """按日期范围查询，未查验的优先"""
        return list(
            InspectionRecord
            .select(InspectionRecord, Ingredient)
            .join(Ingredient)
            .where(
                (InspectionRecord.inspection_date >= date_from)
                & (InspectionRecord.inspection_date <= date_to)
            )
            .order_by(
                # 未查验的排前面
                ((InspectionRecord.inspector == "") | (InspectionRecord.inspector.is_null())),
                InspectionRecord.inspection_date.desc(),
                InspectionRecord.created_at.desc(),
            )
        )

    def batch_upsert(self, records: List[dict]) -> tuple:
        """批量保存：按 stock_in_id 判断存在则更新否则新增
        返回: (新增数量, 更新数量)
        """
        insert_count = 0
        update_count = 0
        for record in records:
            stock_in_id = record.get("stock_in")
            if stock_in_id:
                existing = self.get_by_stock_in_id(stock_in_id)
                if existing:
                    # 更新
                    update_fields = {k: v for k, v in record.items()
                                     if k in self.ALLOWED_FIELDS and k != "stock_in"}
                    if update_fields:
                        self.update(existing.id, **update_fields)
                    update_count += 1
                else:
                    # 新增
                    create_fields = {k: v for k, v in record.items() if k in self.ALLOWED_FIELDS}
                    InspectionRecord.create(**create_fields)
                    insert_count += 1
            else:
                # 无 stock_in_id，直接新增
                create_fields = {k: v for k, v in record.items()
                                 if k in self.ALLOWED_FIELDS and k != "stock_in"}
                InspectionRecord.create(**create_fields)
                insert_count += 1
        return insert_count, update_count


class InspectorRepository(BaseRepository[Inspector]):
    model = Inspector
    ALLOWED_FIELDS = {"name", "phone", "department", "status"}

    def get_all_ordered(self, order_field: str = "name", limit: int = 500) -> List[Inspector]:
        return list(Inspector.select().order_by(Inspector.name))

    def get_active(self) -> List[Inspector]:
        return list(Inspector.select().where(Inspector.status == 1).order_by(Inspector.name))

    def get_by_name(self, name: str) -> Optional[Inspector]:
        return Inspector.get_or_none(Inspector.name == name)
