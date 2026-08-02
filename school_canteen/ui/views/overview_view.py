"""
概览视图 - 仪表盘统计
顶部展示关键指标卡片，下方按分类汇总库存
"""
from PyQt6.QtWidgets import (
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)

from ..base_page import BasePage
from ..widgets.stat_card import StatCard, StatCardRow
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class OverviewView(BasePage):
    """概览视图 - 仪表盘"""

    def __init__(self, report_service, title, parent=None):
        self.report_service = report_service
        super().__init__(title=title, parent=parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        # 顶部统计卡片行
        self.card_total = StatCard("食材总数", "0", ui.color_blue)
        self.card_value = StatCard("库存总值", "¥0.00", ui.color_orange)
        self.card_low = StatCard("低库存预警", "0", ui.color_red)
        self.card_categories = StatCard("分类数量", "0", ui.color_green)
        self.card_row = StatCardRow([
            self.card_total, self.card_value,
            self.card_low, self.card_categories,
        ])
        self.content_layout.addWidget(self.card_row)

        # 分类库存统计表格
        section_label = QLabel("分类库存统计")
        section_label.setObjectName("sectionLabel")
        self.content_layout.addWidget(section_label)

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(4)
        self.category_table.setHorizontalHeaderLabels([
            "分类名称", "食材数量", "库存总量", "安全库存总量"
        ])
        self.category_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.category_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        header = self.category_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.category_table.verticalHeader().setVisible(False)
        self.category_table.setAlternatingRowColors(True)
        self.content_layout.addWidget(self.category_table)

        self.content_layout.addStretch()

    def refresh(self):
        """刷新页面数据"""
        # 卡片数据
        try:
            stats = self.report_service.get_overview_stats()
        except Exception:
            stats = {}

        self.card_total.set_value(str(stats.get("total_ingredients", 0)))
        self.card_value.set_value(f"¥{stats.get('inventory_value', 0):,.2f}")
        self.card_low.set_value(str(stats.get("low_stock_count", 0)))
        self.card_categories.set_value(str(stats.get("categories_count", 0)))

        # 分类库存统计
        try:
            summary = self.report_service.get_stock_summary()
        except Exception:
            summary = []

        self.category_table.setRowCount(len(summary))
        for i, row in enumerate(summary):
            self.category_table.setItem(
                i, 0, QTableWidgetItem(str(row.get("category_name", "")))
            )
            self.category_table.setItem(
                i, 1, QTableWidgetItem(str(row.get("ingredient_count", 0)))
            )
            total_stock = row.get("total_stock") or 0
            total_safety = row.get("total_safety_stock") or 0
            self.category_table.setItem(
                i, 2, QTableWidgetItem(f"{total_stock:.2f}")
            )
            self.category_table.setItem(
                i, 3, QTableWidgetItem(f"{total_safety:.2f}")
            )

    def on_show(self):
        """页面切换显示时刷新数据"""
        self.refresh()
