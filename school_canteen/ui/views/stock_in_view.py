"""
入库管理页面 - 食材入库登记、销售订单导入、记录导出
"""
from PyQt6.QtWidgets import (
    QHBoxLayout, QFormLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
    QLineEdit, QLabel, QGroupBox, QHeaderView, QMessageBox,
    QDateTimeEdit,
)
from PyQt6.QtCore import Qt, QDateTime

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ...config import get_config
from ...core.session import Session
from ...core.exceptions import (
    NotFoundError, ValidationError, BusinessRuleError,
)

cfg = get_config()
ui = cfg.ui


class StockInView(BasePage):
    """入库管理页面"""

    def __init__(self, stock_service, excel_service, title, parent=None):
        self.stock_service = stock_service
        self.excel_service = excel_service
        super().__init__(title, parent)
        self._setup_ui()
        self._load_ingredients()
        self._load_suppliers()
        self._load_data()

    # ===== UI 构建 =====

    def _setup_ui(self):
        # 顶部操作栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(ui.button_spacing)

        self.btn_add = QPushButton("新增入库")
        apply_css_class(self.btn_add, "primary")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self._do_stock_in)

        self.btn_import = QPushButton("导入销售订单")
        apply_css_class(self.btn_import, "success")
        self.btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import.clicked.connect(self._import_sales_orders)

        self.btn_export = QPushButton("导出记录")
        apply_css_class(self.btn_export, "secondary")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.clicked.connect(self._export_records)

        self.date_from = QDateTimeEdit()
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setCalendarPopup(True)
        self.date_from.setDateTime(QDateTime.currentDateTime().addDays(-30))

        self.date_to = QDateTimeEdit()
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setCalendarPopup(True)
        self.date_to.setDateTime(QDateTime.currentDateTime())

        self.btn_refresh = QPushButton("刷新")
        apply_css_class(self.btn_refresh, "secondary")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._load_data)

        top_bar.addWidget(self.btn_add)
        top_bar.addWidget(self.btn_import)
        top_bar.addWidget(self.btn_export)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("日期范围:"))
        top_bar.addWidget(self.date_from)
        top_bar.addWidget(QLabel("至"))
        top_bar.addWidget(self.date_to)
        top_bar.addWidget(self.btn_refresh)
        self.content_layout.addLayout(top_bar)

        # 新增入库表单
        form_group = QGroupBox("新增入库")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 第一行：食材、数量
        row1 = QHBoxLayout()
        self.ingredient_combo = QComboBox()
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self._update_total)

        row1.addWidget(QLabel("食材*:"))
        row1.addWidget(self.ingredient_combo, 1)
        row1.addWidget(QLabel("数量*:"))
        row1.addWidget(self.quantity_spin)
        form_layout.addRow(row1)

        # 第二行：单价、总价、供应商、批次号
        row2 = QHBoxLayout()
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        self.price_spin.setPrefix("¥ ")
        self.price_spin.valueChanged.connect(self._update_total)

        self.total_label = QLabel("¥0.00")
        self.total_label.setStyleSheet(
            f"font-weight: 600; color: {ui.color_blue};"
        )

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- 请选择供应商 --", None)

        self.batch_edit = QLineEdit()
        self.batch_edit.setPlaceholderText("批次号")

        row2.addWidget(QLabel("单价*:"))
        row2.addWidget(self.price_spin)
        row2.addWidget(QLabel("总价:"))
        row2.addWidget(self.total_label)
        row2.addSpacing(10)
        row2.addWidget(QLabel("供应商:"))
        row2.addWidget(self.supplier_combo, 1)
        row2.addWidget(QLabel("批次号:"))
        row2.addWidget(self.batch_edit)
        form_layout.addRow(row2)

        # 第三行：生产日期、保质期、操作人
        row3 = QHBoxLayout()
        self.production_date = QDateTimeEdit()
        self.production_date.setDisplayFormat("yyyy-MM-dd")
        self.production_date.setCalendarPopup(True)
        self.production_date.setDateTime(QDateTime.currentDateTime())

        self.expiry_date = QDateTimeEdit()
        self.expiry_date.setDisplayFormat("yyyy-MM-dd")
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDateTime(QDateTime.currentDateTime().addDays(30))

        self.operator_edit = QLineEdit()
        self.operator_edit.setPlaceholderText("操作人")
        self.operator_edit.setText(Session.display_name)

        row3.addWidget(QLabel("生产日期:"))
        row3.addWidget(self.production_date)
        row3.addWidget(QLabel("保质期至:"))
        row3.addWidget(self.expiry_date)
        row3.addSpacing(10)
        row3.addWidget(QLabel("操作人:"))
        row3.addWidget(self.operator_edit, 1)
        form_layout.addRow(row3)

        # 第四行：备注
        row4 = QHBoxLayout()
        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("备注")
        row4.addWidget(QLabel("备注:"))
        row4.addWidget(self.remark_edit, 1)
        form_layout.addRow(row4)

        # 入库时间（仅特权角色可自定义，用于回溯录入历史入库）
        self.stock_in_time = None
        if Session.can_set_custom_time:
            row_time = QHBoxLayout()
            self.stock_in_time = QDateTimeEdit()
            self.stock_in_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            self.stock_in_time.setCalendarPopup(True)
            self.stock_in_time.setDateTime(QDateTime.currentDateTime())
            row_time.addWidget(QLabel("入库时间:"))
            row_time.addWidget(self.stock_in_time)
            row_time.addStretch()
            form_layout.addRow(row_time)

        self.content_layout.addWidget(form_group)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材名称", "数量", "单价", "总价", "供应商",
            "批次号", "生产日期", "保质期", "操作人", "备注", "时间", "操作",
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 100)
        self.table.setColumnWidth(8, 100)
        self.table.setColumnWidth(9, 80)
        self.table.setColumnWidth(10, 120)
        self.table.setColumnWidth(11, 140)
        self.table.setColumnWidth(12, 80)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.content_layout.addWidget(self.table, 1)

    # ===== 数据加载 =====

    def _load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = self.stock_service.ingredient_repo.get_all_with_relations()
        for ing in ingredients:
            self.ingredient_combo.addItem(
                f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id
            )

    def _load_suppliers(self):
        self.supplier_combo.clear()
        self.supplier_combo.addItem("-- 请选择供应商 --", None)
        suppliers = self.stock_service.supplier_repo.get_active()
        for s in suppliers:
            self.supplier_combo.addItem(s.name, s.id)

    def _load_data(self):
        try:
            records = self.stock_service.get_stock_in_records()
            self._populate_table(records)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")

    def _populate_table(self, records):
        suppliers = {
            s.id: s.name for s in self.stock_service.supplier_repo.get_all_ordered()
        }
        date_from = self.date_from.dateTime().toString("yyyy-MM-dd")
        date_to = self.date_to.dateTime().toString("yyyy-MM-dd")

        filtered = []
        for r in records:
            record_date = str(r.created_at)[:10]
            if date_from <= record_date <= date_to:
                filtered.append(r)

        self.table.setRowCount(len(filtered))
        for i, r in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.id)))
            self.table.setItem(i, 1, QTableWidgetItem(r.ingredient.name if r.ingredient else ""))
            self.table.setItem(i, 2, QTableWidgetItem(str(r.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(f"¥{r.unit_price:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"¥{r.total_price:.2f}"))
            supplier_name = suppliers.get(r.supplier_id, "-") if r.supplier_id else "-"
            self.table.setItem(i, 5, QTableWidgetItem(supplier_name))
            self.table.setItem(i, 6, QTableWidgetItem(r.batch_number or ""))
            self.table.setItem(i, 7, QTableWidgetItem(str(r.production_date or "")))
            self.table.setItem(i, 8, QTableWidgetItem(str(r.expiry_date or "")))
            self.table.setItem(i, 9, QTableWidgetItem(r.operator or ""))
            self.table.setItem(i, 10, QTableWidgetItem(r.remark or ""))
            self.table.setItem(i, 11, QTableWidgetItem(str(r.created_at)[:19]))

            btn_delete = QPushButton("删除")
            apply_css_class(btn_delete, "danger")
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.clicked.connect(
                lambda checked, rid=r.id: self._delete_record(rid)
            )
            self.table.setCellWidget(i, 12, btn_delete)

    # ===== 业务操作 =====

    def _update_total(self):
        total = self.quantity_spin.value() * self.price_spin.value()
        self.total_label.setText(f"¥{total:.2f}")

    def _do_stock_in(self):
        ingredient_id = self.ingredient_combo.currentData()
        quantity = self.quantity_spin.value()
        price = self.price_spin.value()

        if not ingredient_id or quantity <= 0 or price < 0:
            QMessageBox.warning(self, "警告", "请填写完整的入库信息")
            return

        try:
            created_at = (
                self.stock_in_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
                if self.stock_in_time else None
            )
            self.stock_service.stock_in(
                ingredient_id=ingredient_id,
                quantity=quantity,
                unit_price=price,
                supplier_id=self.supplier_combo.currentData(),
                batch_number=self.batch_edit.text(),
                production_date=self.production_date.dateTime().toString("yyyy-MM-dd"),
                expiry_date=self.expiry_date.dateTime().toString("yyyy-MM-dd"),
                operator=self.operator_edit.text(),
                remark=self.remark_edit.text(),
                created_at=created_at,
            )
            QMessageBox.information(self, "提示", "入库成功")
            self._load_data()
            self._load_ingredients()
            self.quantity_spin.setValue(1)
            self.price_spin.setValue(0)
            self.batch_edit.clear()
            self.remark_edit.clear()
            self.data_changed.emit("stock_in")
        except (ValidationError, NotFoundError, BusinessRuleError) as e:
            QMessageBox.critical(self, "错误", f"入库失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"入库操作异常: {e}")

    def _import_sales_orders(self):
        try:
            success, msg = self.excel_service.import_sales_orders(self)
            if success:
                QMessageBox.information(self, "提示", msg)
                self._load_data()
                self._load_ingredients()
                self.data_changed.emit("stock_in")
            else:
                QMessageBox.warning(self, "导入失败", msg)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入异常: {e}")

    def _export_records(self):
        try:
            success = self.excel_service.export_stock_in_records(self)
            if success:
                QMessageBox.information(self, "提示", "导出成功")
            else:
                QMessageBox.warning(self, "警告", "导出失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出异常: {e}")

    def _delete_record(self, record_id):
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除该入库记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.stock_service.delete_stock_in(record_id)
            QMessageBox.information(self, "提示", "删除成功")
            self._load_data()
            self.data_changed.emit("stock_in")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    # ===== 页面回调 =====

    def refresh(self):
        self._load_data()
        self._load_ingredients()

    def on_show(self):
        self._load_data()
        self._load_ingredients()
