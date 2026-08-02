"""
日志仓储与报表查询仓储
"""
from typing import List, Optional
from peewee import fn, SQL, JOIN
from ..models import OperationLog, User, StockIn, StockOut, Ingredient, Category
from .base import BaseRepository


class LogRepository(BaseRepository[OperationLog]):
    model = OperationLog

    def add(self, user_id: Optional[int], action: str, target_type: str = "",
            target_id: int = 0, details: str = ""):
        OperationLog.create(
            user=user_id, action=action, target_type=target_type,
            target_id=target_id, details=details,
        )

    def get_all_with_user(self, limit: int = 500) -> List[OperationLog]:
        return list(
            OperationLog
            .select(OperationLog, User)
            .join(User, JOIN.LEFT_OUTER, on=(OperationLog.user == User.id))
            .order_by(OperationLog.created_at.desc())
            .limit(limit)
        )

    def get_by_action_keyword(self, keyword: str, limit: int = 10) -> List[OperationLog]:
        return list(
            OperationLog
            .select(OperationLog, User)
            .join(User, JOIN.LEFT_OUTER, on=(OperationLog.user == User.id))
            .where(OperationLog.action.contains(keyword))
            .order_by(OperationLog.created_at.desc())
            .limit(limit)
        )

    def delete_all(self) -> int:
        return OperationLog.delete().execute()


class ReportRepository:
    """报表查询仓储 - 复杂聚合查询"""

    def get_stock_summary(self) -> List[dict]:
        """按分类统计食材数量、库存总量、安全库存总量"""
        query = (
            Category
            .select(
                Category.name.alias("category_name"),
                fn.COUNT(Ingredient.id).alias("ingredient_count"),
                fn.SUM(Ingredient.current_stock).alias("total_stock"),
                fn.SUM(Ingredient.safety_stock).alias("total_safety_stock"),
            )
            .join(Ingredient, on=(Ingredient.category == Category.id))
            .where(Ingredient.status == 1)
            .group_by(Category.id)
            .order_by(Category.name)
        )
        return list(query.dicts())

    def get_inventory_value(self) -> float:
        """库存总值 = Σ(当前库存 × 加权平均单价)"""
        ingredients = list(
            Ingredient
            .select(Ingredient.id, Ingredient.current_stock)
            .where((Ingredient.status == 1) & (Ingredient.current_stock > 0))
        )
        total = 0.0
        for ing in ingredients:
            weighted = (
                StockIn
                .select(
                    fn.COALESCE(
                        fn.SUM(StockIn.total_price) / fn.NULLIF(fn.SUM(StockIn.quantity), 0),
                        0,
                    )
                )
                .where(StockIn.ingredient == ing.id)
                .scalar()
            ) or 0
            total += ing.current_stock * weighted
        return total

    def get_expiry_warnings(self, days: int = 7) -> List[dict]:
        """即将过期的食材预警"""
        query = (
            StockIn
            .select(
                StockIn.id, Ingredient.name.alias("ingredient_name"),
                StockIn.batch_number, StockIn.quantity, StockIn.expiry_date,
                StockIn.created_at,
                (fn.julianday(StockIn.expiry_date) - fn.julianday(SQL("date('now')"))).alias("days_left"),
            )
            .join(Ingredient)
            .where(
                StockIn.expiry_date.is_null(False)
                & (StockIn.expiry_date != "")
                & (fn.julianday(StockIn.expiry_date) - fn.julianday(SQL("date('now')")) <= days)
                & (fn.julianday(StockIn.expiry_date) - fn.julianday(SQL("date('now')")) >= 0)
            )
            .order_by(SQL("days_left"))
        )
        return list(query.dicts())

    def get_expired_items(self) -> List[dict]:
        """已过期食材"""
        query = (
            StockIn
            .select(
                StockIn.id, Ingredient.name.alias("ingredient_name"),
                StockIn.batch_number, StockIn.quantity, StockIn.expiry_date,
                StockIn.created_at,
            )
            .join(Ingredient)
            .where(
                StockIn.expiry_date.is_null(False)
                & (StockIn.expiry_date != "")
                & (fn.julianday(StockIn.expiry_date) < fn.julianday(SQL("date('now')")))
            )
            .order_by(StockIn.expiry_date.desc())
        )
        return list(query.dicts())

    def clear_stock_records(self):
        """清理出入库记录（先删查验记录以解除对 stock_in 的外键引用）"""
        from ..models import InspectionRecord
        InspectionRecord.delete().execute()
        StockIn.delete().execute()
        StockOut.delete().execute()

    def clear_inspection_records(self):
        from ..models import InspectionRecord
        InspectionRecord.delete().execute()

    def clear_inventory_records(self):
        from ..models import InventoryCheck
        InventoryCheck.delete().execute()

    def reset_all_stock(self):
        """重置所有食材库存为0"""
        Ingredient.update(current_stock=0).execute()

    def reset_autoincrement(self):
        """重置自增ID序列。

        peewee 默认 AutoField 不生成 AUTOINCREMENT 关键字，
        SQLite 不会创建 sqlite_sequence 表，直接执行会抛
        'no such table: sqlite_sequence'。因此尝试执行、失败则静默跳过。
        """
        from ..database import db
        tables = ["stock_in", "stock_out", "inventory_check", "operation_logs",
                  "inspection_records", "ingredients", "suppliers", "categories",
                  "category_mappings", "inspectors"]
        try:
            with db.atomic():
                for table in tables:
                    db.execute_sql(
                        "DELETE FROM sqlite_sequence WHERE name = ?", (table,))
        except Exception:
            pass
