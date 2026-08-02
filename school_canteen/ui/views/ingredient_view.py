"""
食材管理视图 - 食材 CRUD、批量操作、Excel 导入导出
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QComboBox,
    QFormLayout, QDoubleSpinBox, QLabel, QMessageBox, QFileDialog,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ..base_dialog import BaseDialog
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class IngredientEditDialog(BaseDialog):
    """食材编辑/新增对话框"""

    def __init__(self, category_service, supplier_service,
                 ingredient=None, parent=None):
        title = "编辑食材" if ingredient else "新增食材"
        super().__init__(parent, title)
        self.category_service = category_service
        self.supplier_service = supplier_service
        self.ingredient = ingredient
        self._setup_ui()
        if ingredient is not None:
            self._load_data()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(ui.operation_spacing)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入食材名称")

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItem("-- 请选择 --", None)
        try:
            for cat in self.category_service.get_all():
                self.category_combo.addItem(cat.name, cat.id)
        except Exception:
            pass

        self.spec_edit = QLineEdit()
        self.spec_edit.setPlaceholderText("如：500g/袋")

        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("如：千克、个、袋")

        self.safety_stock_spin = QDoubleSpinBox()
        self.safety_stock_spin.setMaximum(999999)
        self.safety_stock_spin.setDecimals(2)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.supplier_combo.addItem("-- 请选择 --", None)
        try:
            for sup in self.supplier_service.get_active():
                self.supplier_combo.addItem(sup.name, sup.id)
        except Exception:
            pass

        for w in [self.name_edit, self.category_combo, self.spec_edit,
                  self.unit_edit, self.safety_stock_spin, self.supplier_combo]:
            self.setup_form_field(w)

        layout.addRow("食材名称*:", self.name_edit)
        layout.addRow("分类*:", self.category_combo)
        layout.addRow("规格:", self.spec_edit)
        layout.addRow("单位*:", self.unit_edit)
        layout.addRow("安全库存:", self.safety_stock_spin)
        layout.addRow("供应商:", self.supplier_combo)

        self.btn_save = self.make_button("保存", css_class="success")
        self.btn_cancel = self.make_button("取消", css_class="secondary")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addRow("", self.create_button_layout(self.btn_save, self.btn_cancel))

    def _load_data(self):
        ing = self.ingredient
        self.name_edit.setText(ing.name or "")
        if ing.category:
            idx = self.category_combo.findData(ing.category.id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            else:
                self.category_combo.setEditText(ing.category.name)
        self.spec_edit.setText(ing.specification or "")
        self.unit_edit.setText(ing.unit or "")
        self.safety_stock_spin.setValue(ing.safety_stock or 0)
        if ing.supplier:
            idx = self.supplier_combo.findData(ing.supplier.id)
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
            else:
                self.supplier_combo.setEditText(ing.supplier.name)

    def get_data(self) -> dict:
        cat_text = self.category_combo.currentText().strip()
        sup_text = self.supplier_combo.currentText().strip()
        return {
            "name": self.name_edit.text().strip(),
            "category_name": cat_text if cat_text and cat_text != "-- 请选择 --" else None,
            "specification": self.spec_edit.text().strip(),
            "unit": self.unit_edit.text().strip() or "个",
            "safety_stock": self.safety_stock_spin.value(),
            "supplier_name": sup_text if sup_text and sup_text != "-- 请选择 --" else None,
        }


class IngredientView(BasePage):
    """食材管理页面"""

    def __init__(self, ingredient_service, category_service,
                 supplier_service, excel_service, title, parent=None):
        self.ingredient_service = ingredient_service
        self.category_service = category_service
        self.supplier_service = supplier_service
        self.excel_service = excel_service
        self._all_ingredients = []
        self._filtered_ingredients = []
        super().__init__(title, parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 顶部操作栏
        top_layout = QHBoxLayout()
        top_layout.setSpacing(ui.button_spacing)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索食材名称...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        top_layout.addWidget(self.search_edit, 1)

        self.btn_add = QPushButton("新增食材")
        apply_css_class(self.btn_add, "primary")
        self.btn_add.clicked.connect(self._add_ingredient)
        top_layout.addWidget(self.btn_add)

        self.btn_import = QPushButton("导入Excel")
        apply_css_class(self.btn_import, "success")
        self.btn_import.clicked.connect(self._import_excel)
        top_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton("导出Excel")
        apply_css_class(self.btn_export, "secondary")
        self.btn_export.clicked.connect(self._export_excel)
        top_layout.addWidget(self.btn_export)

        self.btn_template = QPushButton("下载模板")
        apply_css_class(self.btn_template, "secondary")
        self.btn_template.clicked.connect(self._download_template)
        top_layout.addWidget(self.btn_template)

        self.select_all_check = QCheckBox("全选")
        self.select_all_check.stateChanged.connect(self._on_select_all_changed)
        top_layout.addWidget(self.select_all_check)

        self.btn_batch_delete = QPushButton("批量删除")
        apply_css_class(self.btn_batch_delete, "danger")
        self.btn_batch_delete.clicked.connect(self._batch_delete)
        top_layout.addWidget(self.btn_batch_delete)

        self.add_layout(top_layout)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "复选框", "ID", "食材名称", "分类", "规格", "单位",
            "当前库存", "安全库存", "库存状态", "供应商", "操作",
        ])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnHidden(1, True)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 90)
        self.table.setColumnWidth(8, 80)
        self.table.setColumnWidth(9, 120)
        self.table.setColumnWidth(10, 130)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.add_widget(self.table)

    # ===== 数据加载 =====

    def _load_data(self):
        try:
            self._all_ingredients = self.ingredient_service.get_all_ingredients()
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"获取食材列表失败: {e}")
            self._all_ingredients = []
        self._apply_filter("")

    def _apply_filter(self, keyword: str):
        keyword = keyword.strip().lower()
        if keyword:
            self._filtered_ingredients = [
                ing for ing in self._all_ingredients
                if keyword in (ing.name or "").lower()
            ]
        else:
            self._filtered_ingredients = list(self._all_ingredients)
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(0)
        self.select_all_check.blockSignals(True)
        self.select_all_check.setCheckState(Qt.CheckState.Unchecked)
        self.select_all_check.blockSignals(False)

        ingredients = self._filtered_ingredients
        self.table.setRowCount(len(ingredients))
        for i, ing in enumerate(ingredients):
            # 复选框
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, check_item)

            # ID
            self.table.setItem(i, 1, QTableWidgetItem(str(ing.id)))

            # 食材名称
            self.table.setItem(i, 2, QTableWidgetItem(ing.name or ""))

            # 分类
            category_name = ing.category.name if ing.category else ""
            self.table.setItem(i, 3, QTableWidgetItem(category_name))

            # 规格
            self.table.setItem(i, 4, QTableWidgetItem(ing.specification or ""))

            # 单位
            self.table.setItem(i, 5, QTableWidgetItem(ing.unit or ""))

            # 当前库存
            self.table.setItem(i, 6, QTableWidgetItem(str(ing.current_stock or 0)))

            # 安全库存
            self.table.setItem(i, 7, QTableWidgetItem(str(ing.safety_stock or 0)))

            # 库存状态
            status_item = QTableWidgetItem()
            if (ing.current_stock or 0) > (ing.safety_stock or 0):
                status_item.setText("正常")
                status_item.setForeground(QColor(ui.color_green))
            else:
                status_item.setText("库存不足")
                status_item.setForeground(QColor(ui.color_red))
            self.table.setItem(i, 8, status_item)

            # 供应商
            supplier_name = ing.supplier.name if ing.supplier else ""
            self.table.setItem(i, 9, QTableWidgetItem(supplier_name))

            # 操作
            self.table.setCellWidget(i, 10, self._create_operation_widget(ing.id))

    def _create_operation_widget(self, ingredient_id: int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        btn_edit = QPushButton("编辑")
        apply_css_class(btn_edit, "secondary")
        btn_edit.setFixedWidth(50)
        btn_edit.clicked.connect(
            lambda _, iid=ingredient_id: self._edit_ingredient_by_id(iid))

        btn_delete = QPushButton("删除")
        apply_css_class(btn_delete, "danger")
        btn_delete.setFixedWidth(50)
        btn_delete.clicked.connect(
            lambda _, iid=ingredient_id: self._delete_ingredient_by_id(iid))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        return widget

    # ===== 搜索与全选 =====

    def _on_search_changed(self, text):
        self._apply_filter(text)

    def _on_select_all_changed(self, state):
        checked = state == int(Qt.CheckState.Checked)
        target = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item:
                item.setCheckState(target)

    # ===== 增删改 =====

    def _add_ingredient(self):
        dialog = IngredientEditDialog(
            self.category_service, self.supplier_service, parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "食材名称不能为空")
            return
        try:
            self.ingredient_service.create_ingredient(**data)
            QMessageBox.information(self, "成功", "添加食材成功")
            self._load_data()
            self.data_changed.emit("ingredient")
        except Exception as e:
            QMessageBox.critical(self, "添加失败", str(e))

    def _edit_ingredient_by_id(self, ingredient_id: int):
        try:
            ingredient = self.ingredient_service.get_ingredient(ingredient_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取食材信息失败: {e}")
            return
        dialog = IngredientEditDialog(
            self.category_service, self.supplier_service,
            ingredient=ingredient, parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "食材名称不能为空")
            return
        try:
            self.ingredient_service.update_ingredient(ingredient_id, **data)
            QMessageBox.information(self, "成功", "更新食材成功")
            self._load_data()
            self.data_changed.emit("ingredient")
        except Exception as e:
            QMessageBox.critical(self, "更新失败", str(e))

    def _delete_ingredient_by_id(self, ingredient_id: int):
        # 找到对应行获取名称
        name = ""
        for ing in self._filtered_ingredients:
            if ing.id == ingredient_id:
                name = ing.name or ""
                break
        if not self._confirm(f"确定要删除食材「{name}」吗？\n\n⚠️ 此操作不可撤销！"):
            return
        try:
            self.ingredient_service.delete_ingredient(ingredient_id)
            QMessageBox.information(self, "成功", "删除成功")
            self._load_data()
            self.data_changed.emit("ingredient")
        except Exception as e:
            QMessageBox.critical(self, "删除失败", str(e))

    def _batch_delete(self):
        selected_ids = []
        selected_names = []
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                ing = self._filtered_ingredients[i]
                selected_ids.append(ing.id)
                selected_names.append(ing.name or "")

        if not selected_ids:
            QMessageBox.warning(self, "提示", "请先选择要删除的食材")
            return

        preview = ", ".join(selected_names[:5])
        if len(selected_names) > 5:
            preview += "..."
        if not self._confirm(
            f"确定要删除选中的 {len(selected_ids)} 条食材吗？\n\n"
            f"食材列表：{preview}\n\n⚠️ 警告：此操作不可撤销！"
        ):
            return

        try:
            count = self.ingredient_service.batch_delete(selected_ids)
            fail = len(selected_ids) - count
            QMessageBox.information(
                self, "批量删除完成",
                f"成功删除 {count} 条，失败 {fail} 条")
            self._load_data()
            self.data_changed.emit("ingredient")
        except Exception as e:
            QMessageBox.critical(self, "删除失败", str(e))

    # ===== Excel 导入导出 =====

    def _import_excel(self):
        try:
            result = self.excel_service.import_ingredients(self)
            if result is None:
                return
            if isinstance(result, tuple):
                success, msg = result
            else:
                success, msg = True, str(result)
            if success:
                QMessageBox.information(self, "导入结果", msg)
                self._load_data()
                self.data_changed.emit("ingredient")
            else:
                QMessageBox.warning(self, "导入失败", msg)
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))

    def _export_excel(self):
        try:
            if self.excel_service.export_ingredients(self):
                QMessageBox.information(self, "导出成功", "食材信息已导出！")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _download_template(self):
        try:
            if self.excel_service.create_template(self):
                QMessageBox.information(self, "模板已创建", "导入模板已保存！")
        except Exception as e:
            QMessageBox.critical(self, "创建模板失败", str(e))

    # ===== 工具方法 =====

    def _confirm(self, message: str, title: str = "确认") -> bool:
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def refresh(self):
        self._load_data()

    def on_show(self):
        pass
