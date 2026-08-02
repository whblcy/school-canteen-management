"""
类别映射管理页面 - 提供外部类别到系统分类映射的增删改查
"""
from PyQt6.QtWidgets import (
    QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QMessageBox,
)
from PyQt6.QtCore import Qt

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ..base_dialog import BaseDialog
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class CategoryMappingEditDialog(BaseDialog):
    """类别映射编辑对话框 - 新增/编辑映射关系"""

    def __init__(self, parent=None, mapping=None, category_service=None):
        title = "编辑映射" if mapping else "新增映射"
        super().__init__(parent, title)
        self._mapping = mapping
        self._category_service = category_service
        self._setup_ui()
        self._load_categories()
        if mapping is not None:
            self._load_data()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("外部系统中的类别名称")

        self.target_combo = QComboBox()
        self.target_combo.addItem("-- 请选择 --", None)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("备注说明")

        for w in [self.source_edit, self.target_combo, self.desc_edit]:
            self.setup_form_field(w)

        layout.addRow("源类别名称*:", self.source_edit)
        layout.addRow("目标分类*:", self.target_combo)
        layout.addRow("描述:", self.desc_edit)

        self.btn_save = self.make_button("保存", "success")
        self.btn_cancel = self.make_button("取消", "secondary")
        btn_layout = self.create_button_layout(self.btn_save, self.btn_cancel)
        layout.addRow("", btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _load_categories(self):
        self.target_combo.clear()
        self.target_combo.addItem("-- 请选择 --", None)
        if not self._category_service:
            return
        try:
            categories = self._category_service.get_all() or []
        except Exception:
            categories = []
        for cat in categories:
            self.target_combo.addItem(cat.name, cat.id)

    def _load_data(self):
        self.source_edit.setText(self._mapping.source_category or "")
        target_id = getattr(self._mapping, "target_category_id", None)
        if target_id is not None:
            idx = self.target_combo.findData(target_id)
            if idx >= 0:
                self.target_combo.setCurrentIndex(idx)
        self.desc_edit.setText(getattr(self._mapping, "description", "") or "")

    def get_data(self):
        return {
            "source_category": self.source_edit.text().strip(),
            "target_category_id": self.target_combo.currentData(),
            "description": self.desc_edit.text().strip(),
        }


class CategoryMappingView(BasePage):
    """类别映射管理页面 - 表单 + 表格布局"""

    def __init__(self, mapping_service, category_service, title, parent=None):
        self.mapping_service = mapping_service
        self.category_service = category_service
        super().__init__(title, parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        # 顶部操作区：新增映射 + 刷新
        top_layout = QHBoxLayout()
        top_layout.setSpacing(ui.button_spacing)

        self.btn_add = QPushButton("➕ 新增映射")
        apply_css_class(self.btn_add, "primary")
        self.btn_add.clicked.connect(self._on_add)

        self.btn_refresh = QPushButton("🔄 刷新")
        apply_css_class(self.btn_refresh, "secondary")
        self.btn_refresh.clicked.connect(self.refresh)

        top_layout.addStretch()
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_refresh)
        self.add_layout(top_layout)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "源类别名称", "目标分类", "描述", "操作"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.add_widget(self.table)

    def refresh(self):
        try:
            mappings = self.mapping_service.get_all() or []
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载映射失败: {e}")
            self.table.setRowCount(0)
            return

        # 缓存分类名称映射，便于目标分类名称查找
        category_name_map = {}
        try:
            for cat in (self.category_service.get_all() or []):
                category_name_map[cat.id] = cat.name
        except Exception:
            pass

        self.table.setRowCount(len(mappings))
        for i, m in enumerate(mappings):
            target_name = m.target_category.name if m.target_category else ""
            self.table.setItem(i, 0, QTableWidgetItem(str(m.id)))
            self.table.setItem(i, 1, QTableWidgetItem(m.source_category or ""))
            self.table.setItem(i, 2, QTableWidgetItem(target_name or ""))
            self.table.setItem(i, 3, QTableWidgetItem(getattr(m, "description", "") or ""))
            self._set_operation_buttons(i, m)

    def _set_operation_buttons(self, row, mapping):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        btn_edit = QPushButton("编辑")
        apply_css_class(btn_edit, "success")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(lambda _, m=mapping: self._on_edit(m))

        btn_delete = QPushButton("删除")
        apply_css_class(btn_delete, "danger")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(lambda _, m=mapping: self._on_delete(m))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        layout.addStretch()
        self.table.setCellWidget(row, 4, widget)

    def _on_add(self):
        dialog = CategoryMappingEditDialog(self, category_service=self.category_service)
        if dialog.exec() != CategoryMappingEditDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["source_category"]:
            QMessageBox.warning(self, "提示", "源类别名称不能为空")
            return
        if not data["target_category_id"]:
            QMessageBox.warning(self, "提示", "请选择目标分类")
            return
        try:
            self.mapping_service.create(**data)
            QMessageBox.information(self, "提示", "添加成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def _on_edit(self, mapping):
        dialog = CategoryMappingEditDialog(self, mapping=mapping,
                                           category_service=self.category_service)
        if dialog.exec() != CategoryMappingEditDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["source_category"]:
            QMessageBox.warning(self, "提示", "源类别名称不能为空")
            return
        if not data["target_category_id"]:
            QMessageBox.warning(self, "提示", "请选择目标分类")
            return
        try:
            self.mapping_service.update(mapping.id, **data)
            QMessageBox.information(self, "提示", "更新成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")

    def _on_delete(self, mapping):
        confirm_dlg = BaseDialog(self, "确认删除")
        if not confirm_dlg.confirm(f"确定要删除映射 '{mapping.source_category}' 吗？"):
            return
        try:
            self.mapping_service.delete(mapping.id)
            QMessageBox.information(self, "提示", "删除成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")
