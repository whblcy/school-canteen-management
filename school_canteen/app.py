"""
应用入口 - 初始化数据库、装配 DI 容器、启动应用
"""
import os
import sys
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui import QFont, QIcon

from .config import get_config
from .data.database import initialize_database
from .data.models import seed_default_data
from .data.repositories.user_repository import UserRepository
from .data.repositories.ingredient_repository import IngredientRepository
from .data.repositories.catalog_repository import (
    CategoryRepository, SupplierRepository, CategoryMappingRepository
)
from .data.repositories.stock_repository import (
    StockInRepository, StockOutRepository, InventoryCheckRepository
)
from .data.repositories.inspection_repository import (
    InspectionRecordRepository, InspectorRepository
)
from .data.repositories.report_repository import LogRepository, ReportRepository
from .services.auth_service import AuthService
from .services.ingredient_service import IngredientService
from .services.stock_service import StockService
from .services.inspection_service import InspectionService, InspectorService
from .services.report_service import ReportService
from .services.catalog_service import (
    CategoryService, SupplierService, CategoryMappingService
)
from .services.data_management_service import DataManagementService
from .services.user_service import UserService
from .services.utility_services import (
    LogService, ExcelExportService, ReportExportService
)
from .utils.logging_config import get_logger
from .ui.styles import MAIN_STYLE
from .ui.login_view import LoginDialog
from .ui.main_window import MainWindow


def build_services() -> dict:
    """构建并装配所有服务（手动 DI）"""
    # 仓储层
    user_repo = UserRepository()
    category_repo = CategoryRepository()
    supplier_repo = SupplierRepository()
    ingredient_repo = IngredientRepository()
    stock_in_repo = StockInRepository()
    stock_out_repo = StockOutRepository()
    inventory_repo = InventoryCheckRepository()
    inspection_repo = InspectionRecordRepository()
    inspector_repo = InspectorRepository()
    mapping_repo = CategoryMappingRepository()
    log_repo = LogRepository()
    report_repo = ReportRepository()

    # 服务层
    auth_service = AuthService(user_repo, log_repo)
    category_service = CategoryService(category_repo, log_repo)
    supplier_service = SupplierService(supplier_repo, log_repo)
    mapping_service = CategoryMappingService(mapping_repo, category_repo, log_repo)
    ingredient_service = IngredientService(
        ingredient_repo, category_repo, supplier_repo, log_repo)
    stock_service = StockService(
        ingredient_repo, stock_in_repo, stock_out_repo, inventory_repo,
        category_repo, supplier_repo, log_repo)
    inspection_service = InspectionService(
        inspection_repo, inspector_repo, stock_in_repo, log_repo)
    inspector_service = InspectorService(inspector_repo, log_repo)
    report_service = ReportService(
        ingredient_repo, stock_in_repo, stock_out_repo, report_repo)
    data_mgmt_service = DataManagementService(report_repo, log_repo)
    user_service = UserService(user_repo, log_repo)
    log_service = LogService(log_repo)
    excel_service = ExcelExportService(ingredient_service, stock_service)
    report_export_service = ReportExportService(
        stock_in_repo, stock_out_repo, ingredient_repo,
        inventory_repo, inspection_repo)

    return {
        "auth": auth_service,
        "ingredient": ingredient_service,
        "stock": stock_service,
        "inspection": inspection_service,
        "inspector": inspector_service,
        "report": report_service,
        "category": category_service,
        "supplier": supplier_service,
        "mapping": mapping_service,
        "data_mgmt": data_mgmt_service,
        "user": user_service,
        "log": log_service,
        "excel": excel_service,
        "report_export": report_export_service,
    }


def main():
    """程序入口"""
    logger = get_logger()

    # 高分屏适配：在创建 QApplication 之前声明进程 DPI 感知，
    # 避免 125%/150% 缩放下整窗被系统位图拉伸导致文字/控件发虚。
    try:
        if sys.platform.startswith("win"):
            import ctypes
            try:
                # PerMonitorV2 (Win10 1703+)，最理想的逐显示器缩放
                ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
            except Exception:
                try:
                    # 回退：逐显示器感知 (Win8.1+)
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except Exception:
                    # 回退：系统级感知 (Win7+)
                    ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

    logger.info("=" * 50)
    logger.info(f"启动 {get_config().app_name}")

    # 初始化数据库
    initialize_database()
    seed_default_data()
    logger.info("数据库初始化完成")

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(get_config().app_name)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei", 14))
    app.setStyleSheet(MAIN_STYLE)

    # 应用级图标（所有窗口/对话框继承，登录界面也能正确显示）
    cfg = get_config()
    try:
        icon_path = str(cfg.paths.icon_file)
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"图标文件不存在: {icon_path}")
    except Exception as e:
        logger.warning(f"设置应用图标失败: {e}")

    # 构建服务
    services = build_services()

    # 登录
    login = LoginDialog(services["auth"])
    if login.exec() != QDialog.DialogCode.Accepted:
        logger.info("用户取消登录，退出")
        return 0

    current_user = login.current_user
    logger.info(f"登录成功: {current_user.username}")

    # 显示主窗口
    window = MainWindow(services, current_user)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
