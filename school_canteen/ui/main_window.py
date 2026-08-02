"""
主窗口 - 应用主界面
左侧导航栏 + 右侧 QStackedWidget 内容区
通过 DI 容器注入所有服务，聚合所有业务页面
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from ..config import get_config
from .styles import MAIN_STYLE
from .base_page import BasePage

cfg = get_config()
ui = cfg.ui

# 导航项定义: (显示名, 页面标识)
NAV_ITEMS = [
    ("概览统计", "overview"),
    ("提醒中心", "alerts"),
    ("财务统计", "finance"),
    ("食材管理", "ingredients"),
    ("入库管理", "stock_in"),
    ("出库管理", "stock_out"),
    ("库存盘点", "inventory"),
    ("进货查验", "inspection"),
    ("报表导出", "report_export"),
    ("供应商管理", "suppliers"),
    ("分类管理", "categories"),
    ("类别映射", "mappings"),
    ("系统设置", "settings"),
]


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, services: dict, current_user=None):
        super().__init__()
        self.services = services
        self.current_user = current_user
        self.pages = {}
        self._setup_window()
        self._setup_ui()
        self._setup_navigation()

    def _setup_window(self):
        self.setWindowTitle(f"{cfg.app_name} {cfg.app_version}")
        self.setMinimumSize(ui.window_min_width, ui.window_min_height)
        self.showMaximized()
        icon_path = str(cfg.paths.icon_file)
        try:
            self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧导航
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setFixedWidth(ui.nav_width)
        self.nav_list.setIconSize(QSize(20, 20))
        font = QFont()
        font.setPointSize(11)
        self.nav_list.setFont(font)

        # 右侧内容
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet("background: #f5f5f7;")

        layout.addWidget(self.nav_list)
        layout.addWidget(self.stacked)

    def _setup_navigation(self):
        # 用户管理仅对系统管理员可见
        nav_items = list(NAV_ITEMS)
        if self.current_user and getattr(self.current_user, "role", "") == "admin":
            nav_items.append(("用户管理", "users"))

        for display_name, page_id in nav_items:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, page_id)
            self.nav_list.addItem(item)

        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.nav_list.setCurrentRow(0)

    def _on_nav_changed(self, row):
        if row < 0:
            return
        item = self.nav_list.item(row)
        page_id = item.data(Qt.ItemDataRole.UserRole)
        if page_id not in self.pages:
            self._create_page(page_id)
        self.stacked.setCurrentWidget(self.pages[page_id])
        page = self.pages[page_id]
        if hasattr(page, "on_show"):
            page.on_show()

    def _create_page(self, page_id: str):
        page = self._build_page(page_id)
        if page is None:
            return
        self.pages[page_id] = page
        self.stacked.addWidget(page)

    def _build_page(self, page_id: str) -> BasePage:
        """根据页面标识构建对应页面"""
        s = self.services
        title_map = {pid: name for name, pid in NAV_ITEMS}
        title = title_map.get(page_id, "")

        if page_id == "overview":
            from .views.overview_view import OverviewView
            return OverviewView(s["report"], title)

        elif page_id == "alerts":
            from .views.alerts_view import AlertsView
            return AlertsView(s["report"], title)

        elif page_id == "finance":
            from .views.finance_view import FinanceView
            return FinanceView(s["report"], title)

        elif page_id == "ingredients":
            from .views.ingredient_view import IngredientView
            return IngredientView(s["ingredient"], s["category"],
                                  s["supplier"], s["excel"], title)

        elif page_id == "stock_in":
            from .views.stock_in_view import StockInView
            return StockInView(s["stock"], s["excel"], title)

        elif page_id == "stock_out":
            from .views.stock_out_view import StockOutView
            return StockOutView(s["stock"], s["ingredient"], title)

        elif page_id == "inventory":
            from .views.inventory_view import InventoryView
            return InventoryView(s["stock"], s["ingredient"], title)

        elif page_id == "inspection":
            from .views.inspection_view import InspectionView
            return InspectionView(s["inspection"], s["inspector"],
                                  s["stock"], title)

        elif page_id == "report_export":
            from .views.report_export_view import ReportExportView
            return ReportExportView(s["report_export"], title)

        elif page_id == "suppliers":
            from .views.supplier_view import SupplierView
            return SupplierView(s["supplier"], title)

        elif page_id == "categories":
            from .views.category_view import CategoryView
            return CategoryView(s["category"], title)

        elif page_id == "mappings":
            from .views.category_mapping_view import CategoryMappingView
            return CategoryMappingView(s["mapping"], s["category"], title)

        elif page_id == "settings":
            from .views.settings_view import SettingsView
            view = SettingsView(s["data_mgmt"], s["inspector"],
                                s["auth"], title, self.current_user)
            view.data_cleared.connect(self.refresh_all_pages)
            return view

        elif page_id == "users":
            from .views.user_management_view import UserManagementView
            return UserManagementView(s["user"], "用户管理", self.current_user)

        return None

    def refresh_all_pages(self):
        """数据清理后刷新全部页面"""
        for page in self.pages.values():
            try:
                page.refresh()
            except Exception:
                pass
