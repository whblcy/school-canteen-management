"""
供应商管理页面 - 提供供应商的增删改查与导出界面
"""
import csv

from PyQt6.QtWidgets import (
    QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QWidget, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ..base_dialog import BaseDialog
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class SupplierEditDialog(BaseDialog):
    """供应商编辑对话框 - 新增/编辑供应商信息"""

    def __init__(self, parent=None, supplier=None):
        title = "编辑供应商" if supplier else "新增供应商"
        super().__init__(parent, title)
        self._supplier = supplier
        self._setup_ui()
        if supplier is not None:
            self._load_data()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入供应商名称")
        self.contact_edit = QLineEdit()
        self.contact_edit.setPlaceholderText("请输入联系人")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("请输入联系电话")
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("请输入联系地址")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("请输入邮箱地址")

        for w in [self.name_edit, self.contact_edit, self.phone_edit,
                  self.address_edit, self.email_edit]:
            self.setup_form_field(w)

        layout.addRow("供应商名称*:", self.name_edit)
        layout.addRow("联系人:", self.contact_edit)
        layout.addRow("电话:", self.phone_edit)
        layout.addRow("地址:", self.address_edit)
        layout.addRow("邮箱:", self.email_edit)

        self.btn_save = self.make_button("保存", "success")
        self.btn_cancel = self.make_button("取消", "secondary")
        btn_layout = self.create_button_layout(self.btn_save, self.btn_cancel)
        layout.addRow("", btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _load_data(self):
        self.name_edit.setText(self._supplier.name or "")
        self.contact_edit.setText(self._supplier.contact_person or "")
        self.phone_edit.setText(self._supplier.phone or "")
        self.address_edit.setText(self._supplier.address or "")
        self.email_edit.setText(self._supplier.email or "")

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "contact_person": self.contact_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "email": self.email_edit.text().strip(),
        }


class SupplierView(BasePage):
    """供应商管理页面 - 表单 + 表格布局，支持搜索过滤"""

    def __init__(self, supplier_service, title, parent=None):
        self.supplier_service = supplier_service
        super().__init__(title, parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        # 顶部操作区：搜索 + 新增供应商 + 导出
        top_layout = QHBoxLayout()
        top_layout.setSpacing(ui.button_spacing)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索供应商名称、联系人、电话...")
        self.search_edit.textChanged.connect(self._on_search_changed)

        self.btn_add = QPushButton("➕ 新增供应商")
        apply_css_class(self.btn_add, "primary")
        self.btn_add.clicked.connect(self._on_add)

        self.btn_export = QPushButton("📥 导出")
        apply_css_class(self.btn_export, "secondary")
        self.btn_export.clicked.connect(self._on_export)

        top_layout.addWidget(self.search_edit, 1)
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_export)
        self.add_layout(top_layout)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "供应商名称", "联系人", "电话", "地址", "状态", "操作"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.add_widget(self.table)

    def refresh(self):
        keyword = ""
        if hasattr(self, "search_edit"):
            keyword = self.search_edit.text().lower().strip()
        try:
            suppliers = self.supplier_service.get_all() or []
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载供应商失败: {e}")
            self.table.setRowCount(0)
            return

        if keyword:
            suppliers = [
                s for s in suppliers
                if keyword in (s.name or "").lower()
                or keyword in (s.contact_person or "").lower()
                or keyword in (s.phone or "").lower()
            ]

        self.table.setRowCount(len(suppliers))
        for i, s in enumerate(suppliers):
            status_text = "正常" if getattr(s, "status", 1) else "停用"
            self.table.setItem(i, 0, QTableWidgetItem(str(s.id)))
            self.table.setItem(i, 1, QTableWidgetItem(s.name or ""))
            self.table.setItem(i, 2, QTableWidgetItem(s.contact_person or ""))
            self.table.setItem(i, 3, QTableWidgetItem(s.phone or ""))
            self.table.setItem(i, 4, QTableWidgetItem(s.address or ""))
            self.table.setItem(i, 5, QTableWidgetItem(status_text))
            self._set_operation_buttons(i, s)

    def _set_operation_buttons(self, row, supplier):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        btn_edit = QPushButton("编辑")
        apply_css_class(btn_edit, "success")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(lambda _, s=supplier: self._on_edit(s))

        btn_delete = QPushButton("删除")
        apply_css_class(btn_delete, "danger")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(lambda _, s=supplier: self._on_delete(s))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        layout.addStretch()
        self.table.setCellWidget(row, 6, widget)

    def _on_search_changed(self, _):
        self.refresh()

    def _on_add(self):
        dialog = SupplierEditDialog(self)
        if dialog.exec() != SupplierEditDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "供应商名称不能为空")
            return
        try:
            self.supplier_service.create(**data)
            QMessageBox.information(self, "提示", "添加成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def _on_edit(self, supplier):
        dialog = SupplierEditDialog(self, supplier)
        if dialog.exec() != SupplierEditDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "供应商名称不能为空")
            return
        try:
            self.supplier_service.update(supplier.id, **data)
            QMessageBox.information(self, "提示", "更新成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")

    def _on_delete(self, supplier):
        confirm_dlg = BaseDialog(self, "确认删除")
        if not confirm_dlg.confirm(f"确定要删除供应商 '{supplier.name}' 吗？"):
            return
        try:
            self.supplier_service.delete(supplier.id)
            QMessageBox.information(self, "提示", "删除成功")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def _on_export(self):
        try:
            suppliers = self.supplier_service.get_all() or []
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")
            return

        if not suppliers:
            QMessageBox.information(self, "提示", "没有可导出的数据")
            return

        default_name = "供应商列表.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出供应商列表", default_name, "CSV 文件 (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "供应商名称", "联系人", "电话", "地址", "邮箱", "状态"])
                for s in suppliers:
                    writer.writerow([
                        s.id,
                        s.name or "",
                        s.contact_person or "",
                        s.phone or "",
                        s.address or "",
                        s.email or "",
                        "正常" if getattr(s, "status", 1) else "停用",
                    ])
            QMessageBox.information(self, "提示", f"导出成功: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
