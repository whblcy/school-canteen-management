"""
日志服务与 Excel/报表导出服务
"""
from typing import List, Optional
from ..data.models import OperationLog
from ..data.repositories.report_repository import LogRepository
from ..utils.logging_config import get_logger

logger = get_logger()


class LogService:
    """操作日志服务"""

    def __init__(self, log_repo: LogRepository):
        self.log_repo = log_repo

    def get_all(self, limit: int = 500) -> List[OperationLog]:
        return self.log_repo.get_all_with_user(limit)

    def search(self, keyword: str, limit: int = 10) -> List[OperationLog]:
        return self.log_repo.get_by_action_keyword(keyword, limit)

    def log(self, user_id: Optional[int], action: str,
            target_type: str = "", target_id: int = 0, details: str = ""):
        """记录操作日志"""
        self.log_repo.add(user_id, action, target_type, target_id, details)

    def clear_all(self) -> int:
        count = self.log_repo.delete_all()
        logger.info(f"已清理全部操作日志: {count} 条")
        return count


class ExcelExportService:
    """Excel 导出服务 - 委托给 excel_handler"""

    def __init__(self, ingredient_service=None, stock_service=None):
        self.ingredient_service = ingredient_service
        self.stock_service = stock_service

    def export_ingredients(self, parent, file_path: str = None) -> bool:
        from ..utils.excel_handler import ExcelExporter
        ingredients = self.ingredient_service.get_all_ingredients()
        return ExcelExporter.export_ingredients(parent, ingredients, file_path)

    def export_stock_in_records(self, parent, file_path: str = None) -> bool:
        from ..utils.excel_handler import ExcelExporter
        records = self.stock_service.get_stock_in_records()
        return ExcelExporter.export_stock_records(parent, records, "in", file_path)

    def export_stock_out_records(self, parent, file_path: str = None) -> bool:
        from ..utils.excel_handler import ExcelExporter
        records = self.stock_service.get_stock_out_records()
        return ExcelExporter.export_stock_records(parent, records, "out", file_path)

    def create_template(self, parent) -> bool:
        from ..utils.excel_handler import ExcelExporter
        return ExcelExporter.create_template(parent)

    def import_ingredients(self, parent, file_path: str = None):
        from ..utils.excel_handler import ExcelImporter
        return ExcelImporter.import_ingredients(parent, self.ingredient_service, file_path)

    def import_sales_orders(self, parent, file_path: str = None):
        from ..utils.excel_handler import ExcelImporter
        return ExcelImporter.import_sales_orders(parent, self.stock_service, file_path)


class ReportExportService:
    """监管报表导出服务 - 委托给 report_generator"""

    def __init__(self, stock_in_repo, stock_out_repo, ingredient_repo,
                 inventory_repo, inspection_repo):
        self.stock_in_repo = stock_in_repo
        self.stock_out_repo = stock_out_repo
        self.ingredient_repo = ingredient_repo
        self.inventory_repo = inventory_repo
        self.inspection_repo = inspection_repo

    def export_daily_stock_sheet(self, output_path: str, year: int, month: int, day: int):
        from ..utils.report_generator import ReportGenerator
        ReportGenerator.export_daily_stock_sheet(
            output_path, self.stock_in_repo, self.stock_out_repo, year, month, day)

    def export_monthly_summary(self, output_path: str, year: int, month: int):
        from ..utils.report_generator import ReportGenerator
        ReportGenerator.export_monthly_summary(
            output_path, self.stock_in_repo, self.stock_out_repo, year, month)

    def export_financial_report(self, output_path: str, year: int):
        from ..utils.report_generator import ReportGenerator
        ReportGenerator.export_financial_report(
            output_path, self.stock_in_repo, self.stock_out_repo, year)

    def export_inventory_check_sheet(self, output_path: str, check_records=None):
        from ..utils.report_generator import ReportGenerator
        ReportGenerator.export_inventory_check_sheet(
            output_path, self.ingredient_repo, self.inventory_repo, check_records)

    def export_inspection_report(self, output_path: str, year: int, month: int):
        from ..utils.report_generator import ReportGenerator
        ReportGenerator.export_inspection_report(
            output_path, self.inspection_repo, year, month)
