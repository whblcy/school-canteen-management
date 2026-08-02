"""
报表导出视图 - 监管报表批量导出（非分页签布局）
"""
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QSpinBox, QComboBox, QCheckBox, QGroupBox, QFileDialog, QMessageBox,
    QProgressDialog,
)
from PyQt6.QtCore import Qt

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class ReportExportView(BasePage):
    """报表导出页面"""

    def __init__(self, report_export_service, title, parent=None):
        self.report_export_service = report_export_service
        self._output_dir = ""
        super().__init__(title, parent)
        self._setup_ui()

    def _setup_ui(self):
        # 顶部：年份 + 月份 + 选择导出目录
        top_layout = QHBoxLayout()
        top_layout.setSpacing(ui.button_spacing)

        top_layout.addWidget(QLabel("年份:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(datetime.now().year)
        self.year_spin.setFixedWidth(100)
        top_layout.addWidget(self.year_spin)

        top_layout.addWidget(QLabel("月份:"))
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f"{m} 月", m)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.setFixedWidth(90)
        top_layout.addWidget(self.month_combo)

        top_layout.addWidget(QLabel("日:"))
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 31)
        self.day_spin.setValue(min(datetime.now().day, 28))
        self.day_spin.setFixedWidth(70)
        top_layout.addWidget(self.day_spin)

        top_layout.addSpacing(20)

        self.btn_select_dir = QPushButton("选择导出目录")
        apply_css_class(self.btn_select_dir, "secondary")
        self.btn_select_dir.clicked.connect(self._select_dir)
        top_layout.addWidget(self.btn_select_dir)

        self.dir_label = QLabel("未选择目录")
        self.dir_label.setStyleSheet(f"color: {ui.color_text_secondary};")
        top_layout.addWidget(self.dir_label, 1)

        self.add_layout(top_layout)

        # 报表选择区
        report_group = QGroupBox("选择报表")
        report_layout = QVBoxLayout(report_group)
        report_layout.setSpacing(ui.operation_spacing)

        # 全选/取消全选
        select_row = QHBoxLayout()
        self.btn_select_all = QPushButton("全选")
        apply_css_class(self.btn_select_all, "secondary")
        self.btn_select_all.setFixedWidth(80)
        self.btn_select_all.clicked.connect(self._select_all_reports)
        select_row.addWidget(self.btn_select_all)

        self.btn_unselect_all = QPushButton("取消全选")
        apply_css_class(self.btn_unselect_all, "secondary")
        self.btn_unselect_all.setFixedWidth(80)
        self.btn_unselect_all.clicked.connect(self._unselect_all_reports)
        select_row.addWidget(self.btn_unselect_all)

        self.selected_count_label = QLabel("已选择 0 项")
        self.selected_count_label.setStyleSheet(
            f"color: {ui.color_text_secondary}; font-size: 12px;")
        select_row.addWidget(self.selected_count_label)
        select_row.addStretch()
        report_layout.addLayout(select_row)

        # 报表复选框网格
        self.report_checkboxes = []
        reports = [
            ("daily_stock", "每日出入库表"),
            ("monthly_summary", "每月出入库统计表"),
            ("financial", "财务收支情况表"),
            ("inventory_check", "库存物品盘存盘亏表"),
            ("inspection", "进货查验记录表"),
        ]

        grid = QGridLayout()
        grid.setSpacing(ui.operation_spacing)
        for i, (key, title) in enumerate(reports):
            cb = QCheckBox(title)
            cb.setChecked(True)
            cb.setProperty("report_key", key)
            cb.stateChanged.connect(self._update_selected_count)
            self.report_checkboxes.append(cb)
            grid.addWidget(cb, i // 2, i % 2)
        report_layout.addLayout(grid)

        self.add_widget(report_group)

        # 底部导出按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_export = QPushButton("批量导出")
        apply_css_class(self.btn_export, "primary")
        self.btn_export.setMinimumWidth(160)
        self.btn_export.setMinimumHeight(40)
        self.btn_export.clicked.connect(self._batch_export)
        btn_row.addWidget(self.btn_export)
        self.add_layout(btn_row)

        self.content_layout.addStretch()
        self._update_selected_count()

    # ===== 目录选择 =====

    def _select_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择导出目录", "")
        if directory:
            self._output_dir = directory
            self.dir_label.setText(directory)

    # ===== 报表选择 =====

    def _select_all_reports(self):
        for cb in self.report_checkboxes:
            cb.setChecked(True)

    def _unselect_all_reports(self):
        for cb in self.report_checkboxes:
            cb.setChecked(False)

    def _update_selected_count(self):
        count = sum(1 for cb in self.report_checkboxes if cb.isChecked())
        self.selected_count_label.setText(f"已选择 {count} 项")

    # ===== 批量导出 =====

    def _batch_export(self):
        year = self.year_spin.value()
        month = self.month_combo.currentData()
        day = self.day_spin.value()
        selected = [cb.property("report_key")
                    for cb in self.report_checkboxes if cb.isChecked()]

        if not selected:
            QMessageBox.warning(self, "提示", "请至少选择一个报表")
            return
        if not self._output_dir:
            QMessageBox.warning(self, "提示", "请先选择导出目录")
            return

        report_map = self._build_report_map(year, month, day)

        progress = QProgressDialog("正在导出报表...", "取消", 0,
                                   len(selected), self)
        progress.setWindowTitle("导出进度")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        results = []
        success_count = 0
        fail_count = 0

        for i, key in enumerate(selected):
            if progress.wasCanceled():
                break
            progress.setValue(i)
            progress.setLabelText(f"正在导出: {report_map[key][0]}...")

            name, filename, export_func = report_map[key]
            output_path = os.path.join(self._output_dir, filename)
            try:
                export_func(output_path)
                success_count += 1
                results.append(f"✅ {name} → {filename}")
            except Exception as e:
                fail_count += 1
                results.append(f"❌ {name} - {e}")

        progress.setValue(len(selected))

        summary = (f"导出完成！\n\n成功: {success_count} 个\n失败: {fail_count} 个\n\n"
                   + "\n".join(results))
        if fail_count == 0:
            QMessageBox.information(self, "导出成功", summary)
        else:
            QMessageBox.warning(self, "导出完成", summary)

    def _build_report_map(self, year: int, month: int, day: int) -> dict:
        """构建报表导出映射: key -> (名称, 文件名, 导出函数)"""
        svc = self.report_export_service
        return {
            "daily_stock": (
                "每日出入库表",
                f"每日出入库表_{year}年{month}月{day}日.xlsx",
                lambda p: svc.export_daily_stock_sheet(p, year, month, day),
            ),
            "monthly_summary": (
                "每月出入库统计表",
                f"每月出入库统计表_{year}年{month}月.xlsx",
                lambda p: svc.export_monthly_summary(p, year, month),
            ),
            "financial": (
                "财务收支情况表",
                f"财务收支情况表_{year}年{month}月.xlsx",
                lambda p: svc.export_financial_report(p, year),
            ),
            "inventory_check": (
                "库存物品盘存盘亏表",
                f"库存物品盘存盘亏表_{year}年{month}月.xlsx",
                lambda p: svc.export_inventory_check_sheet(p),
            ),
            "inspection": (
                "进货查验记录表",
                f"进货查验记录表_{year}年{month}月.xlsx",
                lambda p: svc.export_inspection_report(p, year, month),
            ),
        }

    def refresh(self):
        pass

    def on_show(self):
        pass
