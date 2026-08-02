"""
库存盘点页面 - 单条盘点、批量盘点、差异自动计算
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QDoubleSpinBox,
    QLineEdit, QLabel, QGroupBox, QHeaderView, QMessageBox,
    QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ...config import get_config
from ...core.session import Session
from ...core.exceptions import (
    NotFoundError, ValidationError,
)

cfg = get_config()
ui = cfg.ui


class InventoryView(BasePage):
    """库存盘点页面"""

    def __init__(self, stock_service, ingredient_service, title, parent=None):
        self.stock_service = stock_service
        self.ingredient_service = ingredient_service
        super().__init__(title, parent)
        self._setup_ui()
        self._load_ingredients()
        self._load_data()

    # ===== UI 构建 =====

    def _setup_ui(self):
        # 顶部操作栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(ui.button_spacing)

        self.btn_check = QPushButton("开始盘点")
        apply_css_class(self.btn_check, "primary")
        self.btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check.clicked.connect(self._do_inventory_check)

        self.btn_batch = QPushButton("批量盘点")
        apply_css_class(self.btn_batch, "success")
        self.btn_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_batch.clicked.connect(self._open_batch_dialog)

        self.btn_refresh = QPushButton("刷新")
        apply_css_class(self.btn_refresh, "secondary")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._load_data)

        top_bar.addWidget(self.btn_check)
        top_bar.addWidget(self.btn_batch)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_refresh)
        self.content_layout.addLayout(top_bar)

        # 单条盘点表单
        form_group = QGroupBox("新增盘点")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 第一行：食材、系统库存、实际库存
        row1 = QHBoxLayout()
        self.ingredient_combo = QComboBox()

        self.system_stock_label = QLabel("-")
        self.system_stock_label.setStyleSheet(
            f"font-weight: 600; color: {ui.color_blue};"
        )

        self.actual_stock_spin = QDoubleSpinBox()
        self.actual_stock_spin.setMaximum(999999)
        self.actual_stock_spin.setValue(0)
        self.actual_stock_spin.setPrefix("实际: ")

        row1.addWidget(QLabel("食材*:"))
        row1.addWidget(self.ingredient_combo, 1)
        row1.addWidget(QLabel("系统库存:"))
        row1.addWidget(self.system_stock_label)
        row1.addWidget(self.actual_stock_spin)
        form_layout.addRow(row1)

        # 第二行：盘点人、备注
        row2 = QHBoxLayout()
        self.operator_edit = QLineEdit()
        self.operator_edit.setPlaceholderText("盘点人")
        self.operator_edit.setText(Session.display_name)
        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("备注")

        row2.addWidget(QLabel("盘点人:"))
        row2.addWidget(self.operator_edit)
        row2.addWidget(QLabel("备注:"))
        row2.addWidget(self.remark_edit, 1)
        form_layout.addRow(row2)

        self.content_layout.addWidget(form_group)

        # 盘点记录表格
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "复选框", "ID", "食材名称", "分类", "单位",
            "系统库存", "实际库存", "差异", "操作人", "备注", "时间",
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 80)
        self.table.setColumnWidth(9, 120)
        self.table.setColumnWidth(10, 140)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.content_layout.addWidget(self.table, 1)

        self.ingredient_combo.currentIndexChanged.connect(self._on_ingredient_changed)

    # ===== 数据加载 =====

    def _load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = self.ingredient_service.get_all_ingredients()
        for ing in ingredients:
            self.ingredient_combo.addItem(
                f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id
            )
        self._on_ingredient_changed()

    def _load_data(self):
        try:
            records = self.stock_service.get_inventory_records()
            self._populate_table(records)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")

    def _populate_table(self, records):
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            # 复选框
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, check_item)

            self.table.setItem(i, 1, QTableWidgetItem(str(r.id)))
            self.table.setItem(i, 2, QTableWidgetItem(r.ingredient.name if r.ingredient else ""))
            category_name = ""
            if hasattr(r.ingredient, "category") and r.ingredient.category:
                category_name = r.ingredient.category.name
            self.table.setItem(i, 3, QTableWidgetItem(category_name))
            unit = r.ingredient.unit if r.ingredient else ""
            self.table.setItem(i, 4, QTableWidgetItem(unit))
            self.table.setItem(i, 5, QTableWidgetItem(str(r.system_stock)))
            self.table.setItem(i, 6, QTableWidgetItem(str(r.actual_stock)))

            diff_item = QTableWidgetItem(str(r.difference))
            if r.difference != 0:
                diff_item.setForeground(QColor(ui.color_red))
            self.table.setItem(i, 7, diff_item)

            self.table.setItem(i, 8, QTableWidgetItem(r.operator or ""))
            self.table.setItem(i, 9, QTableWidgetItem(r.remark or ""))
            self.table.setItem(i, 10, QTableWidgetItem(str(r.created_at)[:19]))

            if r.difference != 0:
                for col in range(11):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(QColor("#fff5f5"))

    # ===== 业务操作 =====

    def _on_ingredient_changed(self):
        ingredient_id = self.ingredient_combo.currentData()
        if not ingredient_id:
            return
        try:
            ingredient = self.stock_service.ingredient_repo.get_by_id(ingredient_id)
            if ingredient:
                self.system_stock_label.setText(
                    f"{ingredient.current_stock} {ingredient.unit}"
                )
                self.actual_stock_spin.setValue(ingredient.current_stock)
        except Exception:
            pass

    def _do_inventory_check(self):
        ingredient_id = self.ingredient_combo.currentData()
        actual_stock = self.actual_stock_spin.value()

        if not ingredient_id:
            QMessageBox.warning(self, "警告", "请选择食材")
            return

        try:
            self.stock_service.inventory_check(
                ingredient_id=ingredient_id,
                actual_stock=actual_stock,
                operator=self.operator_edit.text(),
                remark=self.remark_edit.text(),
            )
            ingredient = self.stock_service.ingredient_repo.get_by_id(ingredient_id)
            system_stock = ingredient.current_stock if ingredient else 0
            diff = actual_stock - system_stock
            QMessageBox.information(
                self, "盘点完成",
                f"系统库存: {system_stock}\n实际库存: {actual_stock}\n差异: {diff}",
            )
            self._load_data()
            self._load_ingredients()
            self.data_changed.emit("inventory")
        except (ValidationError, NotFoundError) as e:
            QMessageBox.critical(self, "错误", f"盘点失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"盘点操作异常: {e}")

    def _open_batch_dialog(self):
        ingredients = self.ingredient_service.get_all_ingredients()
        if not ingredients:
            QMessageBox.warning(self, "警告", "暂无食材数据")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("批量盘点")
        dialog.setMinimumWidth(800)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setSpacing(10)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_auto = QPushButton("自动填充系统库存")
        apply_css_class(btn_auto, "secondary")
        btn_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm = QPushButton("确认盘点")
        apply_css_class(btn_confirm, "success")
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel = QPushButton("取消")
        apply_css_class(btn_cancel, "secondary")

        btn_row.addWidget(btn_auto)
        btn_row.addStretch()
        btn_row.addWidget(btn_confirm)
        btn_row.addWidget(btn_cancel)
        dialog_layout.addLayout(btn_row)

        # 批量表格
        batch_table = QTableWidget()
        batch_table.setColumnCount(6)
        batch_table.setHorizontalHeaderLabels([
            "食材", "单位", "系统库存", "实际库存", "差异", "ID",
        ])
        batch_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        batch_table.setRowCount(len(ingredients))
        batch_table.setAlternatingRowColors(True)
        batch_table.setColumnHidden(5, True)

        for i, ing in enumerate(ingredients):
            batch_table.setItem(i, 0, QTableWidgetItem(ing.name))
            batch_table.setItem(i, 1, QTableWidgetItem(ing.unit))
            batch_table.setItem(i, 2, QTableWidgetItem(str(ing.current_stock)))
            batch_table.setItem(i, 3, QTableWidgetItem(str(ing.current_stock)))
            batch_table.setItem(i, 4, QTableWidgetItem("0"))

            id_item = QTableWidgetItem(str(ing.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            batch_table.setItem(i, 5, id_item)

        def auto_fill():
            for i in range(batch_table.rowCount()):
                sys_item = batch_table.item(i, 2)
                if sys_item:
                    batch_table.setItem(i, 3, QTableWidgetItem(sys_item.text()))
                    batch_table.setItem(i, 4, QTableWidgetItem("0"))

        def update_diff(item):
            if item.column() == 3:
                row = item.row()
                try:
                    sys_stock = float(batch_table.item(row, 2).text())
                    actual = float(item.text())
                    diff = actual - sys_stock
                    diff_item = QTableWidgetItem(str(diff))
                    if diff != 0:
                        diff_item.setForeground(QColor(ui.color_red))
                    batch_table.setItem(row, 4, diff_item)
                except Exception:
                    pass

        def confirm_batch():
            operator = self.operator_edit.text() or "系统"
            items = []
            for i in range(batch_table.rowCount()):
                id_item = batch_table.item(i, 5)
                actual_item = batch_table.item(i, 3)
                if not id_item or not actual_item:
                    continue
                try:
                    ingredient_id = int(id_item.text())
                    actual_stock = float(actual_item.text())
                except ValueError:
                    continue
                items.append({
                    "ingredient_id": ingredient_id,
                    "actual_stock": actual_stock,
                    "operator": operator,
                    "remark": "批量盘点",
                })

            if not items:
                QMessageBox.warning(dialog, "警告", "没有可盘点的数据")
                return

            success_count = self.stock_service.batch_inventory_check(items)
            QMessageBox.information(
                dialog, "提示", f"批量盘点完成！成功: {success_count} 条"
            )
            self._load_data()
            self._load_ingredients()
            self.data_changed.emit("inventory")
            dialog.accept()

        btn_auto.clicked.connect(auto_fill)
        batch_table.itemChanged.connect(update_diff)
        btn_confirm.clicked.connect(confirm_batch)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec()

    # ===== 页面回调 =====

    def refresh(self):
        self._load_data()
        self._load_ingredients()

    def on_show(self):
        self._load_data()
        self._load_ingredients()
