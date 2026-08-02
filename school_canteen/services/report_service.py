"""
统计与提醒服务 - 财务统计、库存总值、过期预警
"""
from typing import List, Dict
from ..data.repositories.ingredient_repository import IngredientRepository
from ..data.repositories.stock_repository import StockInRepository, StockOutRepository
from ..data.repositories.report_repository import ReportRepository
from ..config import get_config
from ..utils.logging_config import get_logger

logger = get_logger()


class ReportService:
    """统计与提醒服务"""

    def __init__(self, ingredient_repo: IngredientRepository,
                 stock_in_repo: StockInRepository,
                 stock_out_repo: StockOutRepository,
                 report_repo: ReportRepository):
        self.ingredient_repo = ingredient_repo
        self.stock_in_repo = stock_in_repo
        self.stock_out_repo = stock_out_repo
        self.report_repo = report_repo

    # ===== 概览统计 =====

    def get_overview_stats(self) -> dict:
        """概览页统计数据"""
        ingredients = self.ingredient_repo.get_all_with_relations()
        total_count = len(ingredients)
        low_stock_count = sum(
            1 for ing in ingredients
            if ing.current_stock <= ing.safety_stock and ing.status == 1
        )
        inventory_value = self.report_repo.get_inventory_value()
        categories_count = len(self.report_repo.get_stock_summary())
        return {
            "total_ingredients": total_count,
            "low_stock_count": low_stock_count,
            "inventory_value": round(inventory_value, 2),
            "categories_count": categories_count,
        }

    def get_stock_summary(self) -> List[dict]:
        """按分类统计食材"""
        return self.report_repo.get_stock_summary()

    def get_inventory_value(self) -> float:
        """库存总值（加权平均）"""
        return self.report_repo.get_inventory_value()

    # ===== 财务统计 =====

    def get_monthly_finance(self, year: int, month: int) -> dict:
        """月度财务统计"""
        in_amount = self.stock_in_repo.get_total_amount_by_month(year, month)
        out_amount = self.stock_out_repo.get_total_amount_by_month(year, month)
        return {
            "year": year, "month": month,
            "stock_in_amount": round(in_amount, 2),
            "stock_out_amount": round(out_amount, 2),
            "balance": round(in_amount - out_amount, 2),
        }

    def get_yearly_finance(self, year: int) -> List[dict]:
        """年度月度趋势"""
        in_data = self.stock_in_repo.get_yearly_amounts(year)
        out_data = self.stock_out_repo.get_yearly_amounts(year)
        result = []
        for month in range(1, 13):
            month_str = f"{month:02d}"
            result.append({
                "month": month_str,
                "stock_in": round(in_data.get(month_str, 0), 2),
                "stock_out": round(out_data.get(month_str, 0), 2),
            })
        return result

    def get_category_distribution(self, year: int, month: int) -> dict:
        """分类占比"""
        return {
            "in_by_category": self.stock_in_repo.get_category_amounts_by_month(year, month),
            "out_by_category": self.stock_out_repo.get_category_amounts_by_month(year, month),
        }

    def get_supplier_distribution(self, year: int, month: int) -> List[dict]:
        """供应商占比"""
        return self.stock_in_repo.get_supplier_amounts_by_month(year, month)

    # ===== 提醒中心 =====

    def get_low_stock_items(self) -> list:
        """低库存食材"""
        return self.ingredient_repo.get_low_stock()

    def get_expiry_warnings(self, days: int = None) -> List[dict]:
        """即将过期食材"""
        cfg = get_config()
        if days is None:
            days = cfg.business.expiry_warning_days
        return self.report_repo.get_expiry_warnings(days)

    def get_expired_items(self) -> List[dict]:
        """已过期食材"""
        return self.report_repo.get_expired_items()
