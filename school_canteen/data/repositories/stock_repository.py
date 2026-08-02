"""
出入库与盘点仓储 - 纯数据访问，不含事务编排
"""
from typing import Optional, List
from peewee import fn, JOIN, SQL
from ..models import StockIn, StockOut, InventoryCheck, Ingredient, Category
from .base import BaseRepository


class StockInRepository(BaseRepository[StockIn]):
    model = StockIn

    def get_all_with_ingredient(self, limit: int = 100) -> List[StockIn]:
        return list(
            StockIn
            .select(StockIn, Ingredient)
            .join(Ingredient, on=(StockIn.ingredient == Ingredient.id))
            .order_by(StockIn.created_at.desc())
            .limit(limit)
        )

    def find_import_duplicate(self, ingredient_id: int, quantity: float,
                              unit_price: float, batch_number: str = "",
                              remark: str = "", date_str: str = None) -> bool:
        """检测是否已存在完全相同的导入入库记录（防重复导入）。

        匹配条件：同食材 + 同发货日期 + 同数量（浮点近似）+ 同单价（浮点近似）
        + 同单据编号 + 同来源备注。任一不同即视为不同记录，避免误杀合法入库。
        """
        query = StockIn.select().where(StockIn.ingredient == ingredient_id)
        if date_str:
            query = query.where(fn.date(StockIn.created_at) == date_str)
        if batch_number:
            query = query.where(StockIn.batch_number == batch_number)
        if remark is not None:
            query = query.where(StockIn.remark == remark)
        for rec in query:
            if (rec.batch_number or "") != (batch_number or ""):
                continue
            if abs(float(rec.quantity) - float(quantity)) > 1e-6:
                continue
            if abs(float(rec.unit_price) - float(unit_price)) > 1e-4:
                continue
            return True
        return False

    def get_by_date(self, date_str: str) -> List[dict]:
        """按日期查询入库记录（聚合）"""
        query = (
            StockIn
            .select(
                Category.name.alias("category_name"),
                Ingredient.name.alias("ingredient_name"),
                Ingredient.unit.alias("unit"),
                fn.SUM(StockIn.quantity).alias("total_quantity"),
                (fn.SUM(StockIn.total_price) / fn.SUM(StockIn.quantity)).alias("avg_price"),
                fn.SUM(StockIn.total_price).alias("total_amount"),
            )
            .join(Ingredient, on=(StockIn.ingredient == Ingredient.id))
            .join(Category, JOIN.LEFT_OUTER, on=(Ingredient.category == Category.id))
            .where(fn.date(StockIn.created_at) == date_str)
            .group_by(StockIn.ingredient)
            .order_by(Category.name, Ingredient.name)
        )
        return [row for row in query.dicts()]

    def get_monthly(self, year: int, month: int) -> List[dict]:
        query = (
            StockIn
            .select(
                Ingredient.name.alias("ingredient_name"),
                Category.name.alias("category_name"),
                Ingredient.unit,
                fn.SUM(StockIn.quantity).alias("total_quantity"),
                (fn.SUM(StockIn.total_price) / fn.NULLIF(fn.SUM(StockIn.quantity), 0)).alias("avg_price"),
                fn.SUM(StockIn.total_price).alias("total_amount"),
            )
            .join(Ingredient, on=(StockIn.ingredient == Ingredient.id))
            .join(Category, JOIN.LEFT_OUTER, on=(Ingredient.category == Category.id))
            .where((fn.strftime('%Y', StockIn.created_at) == str(year)) & (fn.strftime('%m', StockIn.created_at) == f"{month:02d}"))
            .group_by(StockIn.ingredient)
            .order_by(fn.SUM(StockIn.total_price).desc())
        )
        return list(query.dicts())

    def get_total_amount_by_month(self, year: int, month: int) -> float:
        result = (
            StockIn
            .select(fn.COALESCE(fn.SUM(StockIn.total_price), 0))
            .where((fn.strftime('%Y', StockIn.created_at) == str(year)) & (fn.strftime('%m', StockIn.created_at) == f"{month:02d}"))
            .scalar()
        )
        return result or 0

    def get_yearly_amounts(self, year: int) -> dict:
        """年度月度入库金额 {month_str: amount}"""
        query = (
            StockIn
            .select(
                fn.strftime('%m', StockIn.created_at).alias("month"),
                fn.COALESCE(fn.SUM(StockIn.total_price), 0).alias("amount"),
            )
            .where(fn.strftime('%Y', StockIn.created_at) == str(year))
            .group_by(fn.strftime('%m', StockIn.created_at))
        )
        return {row["month"]: row["amount"] for row in query.dicts()}

    def get_category_amounts_by_month(self, year: int, month: int) -> List[dict]:
        query = (
            StockIn
            .select(
                Category.name.alias("category_name"),
                fn.SUM(StockIn.total_price).alias("amount"),
            )
            .join(Ingredient)
            .join(Category, on=(Ingredient.category == Category.id))
            .where((fn.strftime('%Y', StockIn.created_at) == str(year)) & (fn.strftime('%m', StockIn.created_at) == f"{month:02d}"))
            .group_by(Category.id)
            .order_by(fn.SUM(StockIn.total_price).desc())
        )
        return list(query.dicts())

    def get_supplier_amounts_by_month(self, year: int, month: int) -> List[dict]:
        from ..models import Supplier
        query = (
            StockIn
            .select(
                Supplier.name.alias("supplier_name"),
                fn.SUM(StockIn.total_price).alias("amount"),
            )
            .join(Supplier, on=(StockIn.supplier == Supplier.id))
            .where((fn.strftime('%Y', StockIn.created_at) == str(year)) & (fn.strftime('%m', StockIn.created_at) == f"{month:02d}"))
            .group_by(StockIn.supplier)
            .order_by(fn.SUM(StockIn.total_price).desc())
        )
        return list(query.dicts())

    def get_weighted_price(self, ingredient_id: int) -> float:
        """加权平均单价 = SUM(total_price) / SUM(quantity)"""
        result = (
            StockIn
            .select(
                fn.COALESCE(
                    fn.SUM(StockIn.total_price) / fn.NULLIF(fn.SUM(StockIn.quantity), 0),
                    0,
                )
            )
            .where(StockIn.ingredient == ingredient_id)
            .scalar()
        )
        return result or 0

    def get_last_unit_price(self, ingredient_id: int) -> float:
        """获取最近一次入库单价"""
        record = (
            StockIn
            .select(StockIn.unit_price)
            .where(StockIn.ingredient == ingredient_id)
            .order_by(StockIn.created_at.desc())
            .first()
        )
        return record.unit_price if record else 0

    def has_unexpired_batches(self, ingredient_id: int) -> bool:
        """检查是否有未过期批次"""
        count = (
            StockIn
            .select()
            .where(
                (StockIn.ingredient == ingredient_id)
                & (
                    (StockIn.expiry_date.is_null())
                    | (StockIn.expiry_date == "")
                    | (StockIn.expiry_date >= SQL("date('now')"))
                )
            )
            .count()
        )
        return count > 0

    def has_any_batches(self, ingredient_id: int) -> bool:
        return StockIn.select().where(StockIn.ingredient == ingredient_id).exists()


class StockOutRepository(BaseRepository[StockOut]):
    model = StockOut

    def get_all_with_ingredient(self, limit: int = 100) -> List[StockOut]:
        return list(
            StockOut
            .select(StockOut, Ingredient)
            .join(Ingredient)
            .order_by(StockOut.created_at.desc())
            .limit(limit)
        )

    def get_by_date(self, date_str: str) -> List[dict]:
        query = (
            StockOut
            .select(
                Category.name.alias("category_name"),
                Ingredient.name.alias("ingredient_name"),
                Ingredient.unit.alias("unit"),
                fn.SUM(StockOut.quantity).alias("total_quantity"),
                (fn.SUM(StockOut.total_price) / fn.SUM(StockOut.quantity)).alias("avg_price"),
                fn.SUM(StockOut.total_price).alias("total_amount"),
            )
            .join(Ingredient)
            .join(Category, JOIN.LEFT_OUTER, on=(Ingredient.category == Category.id))
            .where(fn.date(StockOut.created_at) == date_str)
            .group_by(StockOut.ingredient)
            .order_by(Category.name, Ingredient.name)
        )
        return [row for row in query.dicts()]

    def get_monthly(self, year: int, month: int) -> List[dict]:
        query = (
            StockOut
            .select(
                Ingredient.name.alias("ingredient_name"),
                Category.name.alias("category_name"),
                Ingredient.unit,
                fn.SUM(StockOut.quantity).alias("total_quantity"),
                (fn.SUM(StockOut.total_price) / fn.NULLIF(fn.SUM(StockOut.quantity), 0)).alias("avg_price"),
                fn.SUM(StockOut.total_price).alias("total_amount"),
            )
            .join(Ingredient, on=(StockOut.ingredient == Ingredient.id))
            .join(Category, JOIN.LEFT_OUTER, on=(Ingredient.category == Category.id))
            .where((fn.strftime('%Y', StockOut.created_at) == str(year)) & (fn.strftime('%m', StockOut.created_at) == f"{month:02d}"))
            .group_by(StockOut.ingredient)
            .order_by(fn.SUM(StockOut.total_price).desc())
        )
        return list(query.dicts())

    def get_total_amount_by_month(self, year: int, month: int) -> float:
        result = (
            StockOut
            .select(fn.COALESCE(fn.SUM(StockOut.total_price), 0))
            .where((fn.strftime('%Y', StockOut.created_at) == str(year)) & (fn.strftime('%m', StockOut.created_at) == f"{month:02d}"))
            .scalar()
        )
        return result or 0

    def get_yearly_amounts(self, year: int) -> dict:
        query = (
            StockOut
            .select(
                fn.strftime('%m', StockOut.created_at).alias("month"),
                fn.COALESCE(fn.SUM(StockOut.total_price), 0).alias("amount"),
            )
            .where(fn.strftime('%Y', StockOut.created_at) == str(year))
            .group_by(fn.strftime('%m', StockOut.created_at))
        )
        return {row["month"]: row["amount"] for row in query.dicts()}

    def get_category_amounts_by_month(self, year: int, month: int) -> List[dict]:
        query = (
            StockOut
            .select(
                Category.name.alias("category_name"),
                fn.SUM(StockOut.total_price).alias("amount"),
            )
            .join(Ingredient)
            .join(Category, on=(Ingredient.category == Category.id))
            .where((fn.strftime('%Y', StockOut.created_at) == str(year)) & (fn.strftime('%m', StockOut.created_at) == f"{month:02d}"))
            .group_by(Category.id)
            .order_by(fn.SUM(StockOut.total_price).desc())
        )
        return list(query.dicts())


class InventoryCheckRepository(BaseRepository[InventoryCheck]):
    model = InventoryCheck

    def get_all_with_ingredient(self, limit: int = 100) -> List[InventoryCheck]:
        return list(
            InventoryCheck
            .select(InventoryCheck, Ingredient)
            .join(Ingredient)
            .order_by(InventoryCheck.created_at.desc())
            .limit(limit)
        )
