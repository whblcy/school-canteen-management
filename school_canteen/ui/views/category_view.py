"""
食材分类管理页面 - 提供分类的增删改查界面
"""
from PyQt6.QtWidgets import (
    QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QWidget, QMessageBox,
)
from PyQt6.QtCore import Qt

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ..base_dialog import BaseDialog
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class CategoryEditDialog(BaseDialog):
    """分类编辑对话框 - 新增/编辑分类信息"""

    def __init__(self, parent=None, category=None):
        title = "编辑分类" if category else "新增分类"
        super().__init__(parent, title)
        self._category = category
        self._setup_ui()
        if category is not None:
            self._load_data()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入分类名称")
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("请输入分类描述")
        for w in [self.name_edit, self.desc_edit]:
            self.setup_form_field(w)

        layout.addRow("分类名称*:", self.name_edit)
        layout.addRow("描述:", self.desc_edit)

        self.btn_save = self.make_button("保存", "success")
        self.btn_cancel = self.make_button("取消", "secondary")
        btn_layout = self.create_button_layout(self.btn_save, self.btn_cancel)
        layout.addRow("", btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _load_data(self):
        self.name_edit.setText(self._category.name or "")
        self.desc_edit.setText(self._category.description or "")

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
        }


class CategoryView(BasePage):
    """食材分类管理页面 - 表单 + 表格布局"""

    def __init__(self, category_service, title, parent=None):
        self.category_service = category_service
        super().__init__(title, parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        # 顶部操作区：搜索 + 新增 + 刷新
        top_layout = QHBoxLayout()
        top_layout.setSpacing(ui.button_spacing)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索分类名称或描述...")
        self.search_edit.textChanged.connect(self._on_search_changed)

        self.btn_add = QPushButton("➕ 新增")
        apply_css_class(self.btn_add, "primary")
        self.btn_add.clicked.connect(self._on_add)

        self.btn_refresh = QPushButton("🔄 刷新")
        apply_css_class(self.btn_refresh, "secondary")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)

        top_layout.addWidget(self.search_edit, 1)
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_refresh)
        self.add_layout(top_layout)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "分类名称", "描述", "操作"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.add_widget(self.table)

    def refresh(self):
        keyword = ""
        if hasattr(self, "search_edit"):
            keyword = self.search_edit.text().lower().strip()
        try:
            categories = self.category_service.get_all() or []
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载分类失败: {e}")
            self.table.setRowCount(0)
            return

        if keyword:
            categories = [
                c for c in categories
                if keyword in (c.name or "").lower()
                or keyword in (c.description or "").lower()
            ]

        self.table.setRowCount(len(categories))
        for i, cat in enumerate(categories):
            self.table.setItem(i, 0, QTableWidgetItem(str(cat.id)))
            self.table.setItem(i, 1, QTableWidgetItem(cat.name or ""))
            self.table.setItem(i, 2, QTableWidgetItem(cat.description or ""))
            self._set_operation_buttons(i, cat)

    def _set_operation_buttons(self, row, category):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        btn_edit = QPushButton("编辑")
        apply_css_class(btn_edit, "success")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(lambda _, c=category: self._on_edit(c))

        btn_delete = QPushButton("删除")
        apply_css_class(btn_delete, "danger")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(lambda _, c=category: self._on_delete(c))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        layout.addStretch()
        self.table.setCellWidget(row, 3, widget)

    def _on_search_changed(self, _):
        self.refresh()

    def _on_refresh_clicked(self):
        self.search_edit.clear()
        self.refresh()

    def _on_add(self):
        dialog = CategoryEditDialog(self)
        if dialog.exec() != CategoryEditDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "分类名称不能为空")
            return
        try:
            self.category_service.create(**data)
            QMessageBox.information(self, "提示", "添加成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def _on_edit(self, category):
        dialog = CategoryEditDialog(self, category)
        if dialog.exec() != CategoryEditDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "分类名称不能为空")
            return
        try:
            self.category_service.update(category.id, **data)
            QMessageBox.information(self, "提示", "更新成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")

    def _on_delete(self, category):
        confirm_dlg = BaseDialog(self, "确认删除")
        if not confirm_dlg.confirm(f"确定要删除分类 '{category.name}' 吗？"):
            return
        try:
            self.category_service.delete(category.id)
            QMessageBox.information(self, "提示", "删除成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")
