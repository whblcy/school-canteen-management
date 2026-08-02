"""
提醒中心视图 - 低库存预警、即将过期、已过期食材
使用选项卡分区展示三类提醒，行根据紧急程度着色
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTabWidget,
)
from PyQt6.QtGui import QColor

from ..base_page import BasePage
from ..widgets.stat_card import StatCard, StatCardRow
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class AlertsView(BasePage):
    """提醒中心视图"""

    def __init__(self, report_service, title, parent=None):
        self.report_service = report_service
        super().__init__(title=title, parent=parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        # 顶部刷新按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setMinimumWidth(ui.button_min_width)
        self.btn_refresh.clicked.connect(self.refresh)
        top_bar.addWidget(self.btn_refresh)
        self.content_layout.addLayout(top_bar)

        # 三段式选项卡
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_low_stock_tab(), "低库存预警")
        self.tabs.addTab(self._create_expiry_tab(), "即将过期")
        self.tabs.addTab(self._create_expired_tab(), "已过期食材")
        self.content_layout.addWidget(self.tabs)

        self.content_layout.addStretch()

    # ===== 选项卡构建 =====

    def _create_low_stock_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.low_stock_table = self._make_table(
            ["食材名称", "分类", "当前库存", "安全库存", "缺口"]
        )
        layout.addWidget(self.low_stock_table)
        return tab

    def _create_expiry_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.expiry_table = self._make_table(
            ["食材名称", "批次号", "数量", "过期日期", "剩余天数"]
        )
        layout.addWidget(self.expiry_table)
        return tab

    def _create_expired_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.expired_table = self._make_table(
            ["食材名称", "批次号", "数量", "过期日期"]
        )
        layout.addWidget(self.expired_table)
        return tab

    def _make_table(self, headers) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        return table

    # ===== 数据刷新 =====

    def refresh(self):
        """刷新所有提醒数据"""
        self._load_low_stock()
        self._load_expiry_warnings()
        self._load_expired_items()

    def _load_low_stock(self):
        try:
            items = self.report_service.get_low_stock_items()
        except Exception:
            items = []

        self.low_stock_table.setRowCount(len(items))
        for i, ing in enumerate(items):
            name = getattr(ing, "name", "")
            category = getattr(ing, "category_name", "") or ""
            if not category:
                cat = getattr(ing, "category", None)
                if cat is not None:
                    category = getattr(cat, "name", "")
            current = getattr(ing, "current_stock", 0) or 0
            safety = getattr(ing, "safety_stock", 0) or 0
            gap = safety - current

            self.low_stock_table.setItem(i, 0, QTableWidgetItem(str(name)))
            self.low_stock_table.setItem(i, 1, QTableWidgetItem(str(category)))
            self.low_stock_table.setItem(i, 2, QTableWidgetItem(f"{current:.2f}"))
            self.low_stock_table.setItem(i, 3, QTableWidgetItem(f"{safety:.2f}"))
            gap_item = QTableWidgetItem(f"{gap:.2f}")
            gap_item.setForeground(QColor(ui.color_red))
            self.low_stock_table.setItem(i, 4, gap_item)

    def _load_expiry_warnings(self):
        try:
            items = self.report_service.get_expiry_warnings()
        except Exception:
            items = []

        self.expiry_table.setRowCount(len(items))
        for i, item in enumerate(items):
            name = str(item.get("ingredient_name", ""))
            batch = str(item.get("batch_number") or "-")
            quantity = item.get("quantity", 0)
            expiry_date = str(item.get("expiry_date") or "")
            days_left = item.get("days_left")
            try:
                days_int = int(days_left) if days_left is not None else 0
            except (TypeError, ValueError):
                days_int = 0

            self.expiry_table.setItem(i, 0, QTableWidgetItem(name))
            self.expiry_table.setItem(i, 1, QTableWidgetItem(batch))
            self.expiry_table.setItem(i, 2, QTableWidgetItem(str(quantity)))
            self.expiry_table.setItem(i, 3, QTableWidgetItem(expiry_date))
            self.expiry_table.setItem(i, 4, QTableWidgetItem(f"{days_int} 天"))

            # 紧急程度着色：3 天内红色，4-7 天橙色
            if days_int <= 3:
                self._color_row(self.expiry_table, i, 5, ui.color_red)
            elif days_int <= 7:
                self._color_row(self.expiry_table, i, 5, ui.color_orange)

    def _load_expired_items(self):
        try:
            items = self.report_service.get_expired_items()
        except Exception:
            items = []

        self.expired_table.setRowCount(len(items))
        for i, item in enumerate(items):
            name = str(item.get("ingredient_name", ""))
            batch = str(item.get("batch_number") or "-")
            quantity = item.get("quantity", 0)
            expiry_date = str(item.get("expiry_date") or "")

            self.expired_table.setItem(i, 0, QTableWidgetItem(name))
            self.expired_table.setItem(i, 1, QTableWidgetItem(batch))
            self.expired_table.setItem(i, 2, QTableWidgetItem(str(quantity)))
            self.expired_table.setItem(i, 3, QTableWidgetItem(expiry_date))

            # 已过期整行红色
            self._color_row(self.expired_table, i, 4, ui.color_red)

    def _color_row(self, table: QTableWidget, row: int, col_count: int, color: str):
        """为整行设置半透明背景色"""
        bg = QColor(color)
        bg.setAlpha(40)
        for col in range(col_count):
            item = table.item(row, col)
            if item is not None:
                item.setBackground(bg)

    def on_show(self):
        """页面切换显示时刷新数据"""
        self.refresh()
