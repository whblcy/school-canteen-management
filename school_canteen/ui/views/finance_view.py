"""
财务统计视图 - 月度收支卡片、月度明细、年度趋势、分类占比
"""
from datetime import datetime

from PyQt6.QtWidgets import (
    QLabel, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSpinBox, QComboBox,
)
from PyQt6.QtGui import QColor

from ..base_page import BasePage
from ..widgets.stat_card import StatCard, StatCardRow
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class FinanceView(BasePage):
    """财务统计视图"""

    def __init__(self, report_service, title, parent=None):
        self.report_service = report_service
        super().__init__(title=title, parent=parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        # 顶部：年份 + 月份选择 + 查询按钮
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(ui.button_spacing)

        filter_bar.addWidget(QLabel("年份:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2099)
        self.year_spin.setValue(datetime.now().year)
        self.year_spin.setMinimumWidth(100)
        filter_bar.addWidget(self.year_spin)

        filter_bar.addWidget(QLabel("月份:"))
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f"{m} 月", m)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.setMinimumWidth(100)
        filter_bar.addWidget(self.month_combo)

        self.btn_query = QPushButton("查询")
        self.btn_query.setMinimumWidth(ui.button_min_width)
        self.btn_query.clicked.connect(self.refresh)
        filter_bar.addWidget(self.btn_query)

        filter_bar.addStretch()
        self.content_layout.addLayout(filter_bar)

        # Section 1: 当月收支卡片
        self.card_in = StatCard("入库总额", "¥0.00", ui.color_orange)
        self.card_out = StatCard("出库总额", "¥0.00", ui.color_blue)
        self.card_balance = StatCard("结余", "¥0.00", ui.color_green)
        self.finance_card_row = StatCardRow([
            self.card_in, self.card_out, self.card_balance
        ])
        self.content_layout.addWidget(self.finance_card_row)

        # Section 2: 月度明细表格
        self.content_layout.addWidget(
            self._make_section_label("月度明细（按食材）")
        )
        self.monthly_detail_table = self._make_table(
            ["食材名称", "入库数量", "入库金额", "出库数量", "出库金额"]
        )
        self.content_layout.addWidget(self.monthly_detail_table)

        # Section 3: 年度趋势表格
        self.content_layout.addWidget(self._make_section_label("年度趋势"))
        self.yearly_trend_table = self._make_table(
            ["月份", "入库金额", "出库金额", "结余"]
        )
        self.content_layout.addWidget(self.yearly_trend_table)

        # Section 4: 分类占比
        self.content_layout.addWidget(self._make_section_label("分类占比"))
        self.category_table = self._make_table(
            ["分类名称", "金额", "占比(%)"]
        )
        self.content_layout.addWidget(self.category_table)

        self.content_layout.addStretch()

    # ===== 辅助构建 =====

    def _make_section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

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
        """刷新财务数据"""
        year = self.year_spin.value()
        month = self.month_combo.currentData() or 1

        self._load_monthly_finance(year, month)
        self._load_yearly_finance(year)
        self._load_category_distribution(year, month)

    def _load_monthly_finance(self, year: int, month: int):
        # 卡片数据
        try:
            data = self.report_service.get_monthly_finance(year, month)
        except Exception:
            data = {}

        in_amount = data.get("stock_in_amount", 0) or 0
        out_amount = data.get("stock_out_amount", 0) or 0
        balance = data.get("balance", in_amount - out_amount)
        if balance is None:
            balance = in_amount - out_amount

        self.card_in.set_value(f"¥{in_amount:,.2f}")
        self.card_out.set_value(f"¥{out_amount:,.2f}")
        self.card_balance.set_value(f"¥{balance:,.2f}")
        # 结余为负时显示红色
        self.card_balance.set_color(
            ui.color_red if balance < 0 else ui.color_green
        )

        # 月度明细（按食材） - 合并入库与出库明细
        in_items = {}
        out_items = {}
        try:
            for row in self.report_service.stock_in_repo.get_monthly(year, month):
                in_items[row.get("ingredient_name")] = {
                    "quantity": row.get("total_quantity") or 0,
                    "amount": row.get("total_amount") or 0,
                }
        except Exception:
            pass
        try:
            for row in self.report_service.stock_out_repo.get_monthly(year, month):
                out_items[row.get("ingredient_name")] = {
                    "quantity": row.get("total_quantity") or 0,
                    "amount": row.get("total_amount") or 0,
                }
        except Exception:
            pass

        all_names = list(dict.fromkeys(
            list(in_items.keys()) + list(out_items.keys())
        ))
        self.monthly_detail_table.setRowCount(len(all_names))
        for i, name in enumerate(all_names):
            in_data = in_items.get(name, {"quantity": 0, "amount": 0})
            out_data = out_items.get(name, {"quantity": 0, "amount": 0})
            self.monthly_detail_table.setItem(
                i, 0, QTableWidgetItem(str(name))
            )
            self.monthly_detail_table.setItem(
                i, 1, QTableWidgetItem(f"{in_data['quantity']:.2f}")
            )
            self.monthly_detail_table.setItem(
                i, 2, QTableWidgetItem(f"¥{in_data['amount']:,.2f}")
            )
            self.monthly_detail_table.setItem(
                i, 3, QTableWidgetItem(f"{out_data['quantity']:.2f}")
            )
            self.monthly_detail_table.setItem(
                i, 4, QTableWidgetItem(f"¥{out_data['amount']:,.2f}")
            )

    def _load_yearly_finance(self, year: int):
        try:
            data = self.report_service.get_yearly_finance(year)
        except Exception:
            data = []

        self.yearly_trend_table.setRowCount(len(data))
        for i, row in enumerate(data):
            month = row.get("month", "")
            in_amount = row.get("stock_in", 0) or 0
            out_amount = row.get("stock_out", 0) or 0
            balance = in_amount - out_amount

            self.yearly_trend_table.setItem(
                i, 0, QTableWidgetItem(f"{int(month)} 月")
            )
            self.yearly_trend_table.setItem(
                i, 1, QTableWidgetItem(f"¥{in_amount:,.2f}")
            )
            self.yearly_trend_table.setItem(
                i, 2, QTableWidgetItem(f"¥{out_amount:,.2f}")
            )
            bal_item = QTableWidgetItem(f"¥{balance:,.2f}")
            if balance < 0:
                bal_item.setForeground(QColor(ui.color_red))
            self.yearly_trend_table.setItem(i, 3, bal_item)

    def _load_category_distribution(self, year: int, month: int):
        try:
            data = self.report_service.get_category_distribution(year, month)
            in_by_category = data.get("in_by_category", [])
        except Exception:
            in_by_category = []

        total = sum((row.get("amount") or 0) for row in in_by_category)
        self.category_table.setRowCount(len(in_by_category))
        for i, row in enumerate(in_by_category):
            name = str(row.get("category_name", ""))
            amount = row.get("amount") or 0
            pct = (amount / total * 100) if total > 0 else 0
            self.category_table.setItem(i, 0, QTableWidgetItem(name))
            self.category_table.setItem(
                i, 1, QTableWidgetItem(f"¥{amount:,.2f}")
            )
            self.category_table.setItem(
                i, 2, QTableWidgetItem(f"{pct:.1f}")
            )
