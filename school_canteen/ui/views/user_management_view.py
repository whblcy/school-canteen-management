"""
用户管理页面 - 仅系统管理员可访问
提供用户列表、新增用户、修改角色/状态、重置密码、删除用户。
管理员账号受保护：不可禁用、不可改角色、不可删除。
"""
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QComboBox, QLabel, QGroupBox,
)
from PyQt6.QtCore import Qt

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ...config import get_config
from ...core.roles import ROLE_LABELS, ROLE_ADMIN
from ...core.exceptions import ValidationError, DuplicateError

cfg = get_config()
ui = cfg.ui


class UserManagementView(BasePage):
    """用户管理页面（管理员专属）"""

    def __init__(self, user_service, title, current_user=None, parent=None):
        self.user_service = user_service
        self.current_user = current_user
        super().__init__(title, parent)
        self._setup_ui()
        self._load_data()

    # ===== UI 构建 =====

    def _setup_ui(self):
        top_bar = QHBoxLayout()
        top_bar.setSpacing(ui.button_spacing)

        self.btn_add = QPushButton("新增用户")
        apply_css_class(self.btn_add, "primary")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self._add_user)

        self.btn_refresh = QPushButton("刷新")
        apply_css_class(self.btn_refresh, "secondary")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._load_data)

        top_bar.addWidget(self.btn_add)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_refresh)
        self.content_layout.addLayout(top_bar)

        hint = QLabel(
            "说明：库存主管可自定义出入库时间、不受保质期约束；"
            "管理员账号不可被禁用、改角色或删除。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {ui.color_gray}; font-size: 12px;")
        self.content_layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "用户名", "姓名", "角色", "状态", "操作", "ID",
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 220)
        self.table.setColumnHidden(5, True)
        self.table.setAlternatingRowColors(True)
        self.content_layout.addWidget(self.table, 1)

    # ===== 数据加载 =====

    def _load_data(self):
        try:
            users = self.user_service.get_all()
            self.table.setRowCount(len(users))
            for i, u in enumerate(users):
                self.table.setItem(i, 0, QTableWidgetItem(u.username))
                self.table.setItem(i, 1, QTableWidgetItem(u.real_name or ""))
                self.table.setItem(i, 2, QTableWidgetItem(ROLE_LABELS.get(u.role, u.role)))
                status_item = QTableWidgetItem("启用" if u.status == 1 else "禁用")
                if u.status != 1:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, 3, status_item)
                self.table.setItem(i, 5, QTableWidgetItem(str(u.id)))

                btn_edit = QPushButton("编辑")
                apply_css_class(btn_edit, "secondary")
                btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_edit.clicked.connect(lambda _, uid=u.id: self._edit_user(uid))

                btn_pwd = QPushButton("重置密码")
                apply_css_class(btn_pwd, "secondary")
                btn_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_pwd.clicked.connect(lambda _, uid=u.id: self._reset_password(uid))

                btn_del = QPushButton("删除")
                apply_css_class(btn_del, "danger")
                btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_del.clicked.connect(lambda _, uid=u.id: self._delete_user(uid))

                # 管理员不可被改/删
                if u.role == ROLE_ADMIN:
                    btn_edit.setEnabled(False)
                    btn_del.setEnabled(False)

                cell = QHBoxLayout()
                cell.setContentsMargins(0, 0, 0, 0)
                cell.setSpacing(6)
                cell.addWidget(btn_edit)
                cell.addWidget(btn_pwd)
                cell.addWidget(btn_del)
                widget = QGroupBox()
                widget.setLayout(cell)
                widget.setStyleSheet("border: none;")
                self.table.setCellWidget(i, 4, widget)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载用户失败: {e}")

    # ===== 业务操作 =====

    def _add_user(self):
        dialog = self._user_dialog(title="新增用户")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.result
        try:
            self.user_service.create_user(
                username=data["username"],
                password=data["password"],
                real_name=data["real_name"],
                role=data["role"],
                status=data["status"],
            )
            QMessageBox.information(self, "提示", "用户创建成功")
            self._load_data()
        except (ValidationError, DuplicateError) as e:
            QMessageBox.warning(self, "校验失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建用户失败: {e}")

    def _edit_user(self, user_id: int):
        user = self.user_service.get_by_id(user_id)
        if not user:
            return
        dialog = self._user_dialog(title="编辑用户", user=user)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.result
        try:
            self.user_service.update_role(user_id, data["role"])
            self.user_service.update_status(user_id, data["status"])
            # 姓名不在角色/状态里，单独更新
            self.user_service.user_repo.update(user_id, real_name=data["real_name"])
            QMessageBox.information(self, "提示", "保存成功")
            self._load_data()
        except ValidationError as e:
            QMessageBox.warning(self, "校验失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def _reset_password(self, user_id: int):
        dialog = QDialog(self)
        dialog.setWindowTitle("重置密码")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        pwd = QLineEdit()
        pwd.setEchoMode(QLineEdit.EchoMode.Password)
        pwd.setPlaceholderText("至少6位")
        confirm = QLineEdit()
        confirm.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("新密码:", pwd)
        form.addRow("确认新密码:", confirm)
        layout.addLayout(form)
        btn_ok = QPushButton("确定")
        apply_css_class(btn_ok, "success")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("取消")
        apply_css_class(btn_cancel, "secondary")
        btn_cancel.clicked.connect(dialog.reject)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        layout.addLayout(row)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if pwd.text() != confirm.text():
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return
        try:
            self.user_service.reset_password(user_id, pwd.text())
            QMessageBox.information(self, "提示", "密码已重置")
        except ValidationError as e:
            QMessageBox.warning(self, "校验失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重置失败: {e}")

    def _delete_user(self, user_id: int):
        user = self.user_service.get_by_id(user_id)
        if not user:
            return
        if user.role == ROLE_ADMIN:
            QMessageBox.warning(self, "提示", "管理员不可删除")
            return
        reply = QMessageBox.question(
            self, "确认删除", f"确定删除用户「{user.username}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.user_service.delete_user(user_id)
            QMessageBox.information(self, "提示", "删除成功")
            self._load_data()
        except ValidationError as e:
            QMessageBox.warning(self, "提示", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    # ===== 对话框 =====

    def _user_dialog(self, title: str, user=None):
        """新增/编辑共用的对话框，返回带 result 属性的 dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(360)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        username_edit = QLineEdit()
        username_edit.setPlaceholderText("登录用户名")
        real_name_edit = QLineEdit()
        real_name_edit.setPlaceholderText("真实姓名（可选）")
        role_combo = QComboBox()
        for role_value, label in ROLE_LABELS.items():
            role_combo.addItem(label, role_value)
        status_combo = QComboBox()
        status_combo.addItem("启用", 1)
        status_combo.addItem("禁用", 0)
        pwd_edit = QLineEdit()
        pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("用户名*:", username_edit)
        form.addRow("姓名:", real_name_edit)
        form.addRow("角色:", role_combo)
        form.addRow("状态:", status_combo)

        if user is None:
            form.addRow("初始密码*:", pwd_edit)
        else:
            username_edit.setText(user.username)
            username_edit.setEnabled(False)
            real_name_edit.setText(user.real_name or "")
            idx = role_combo.findData(user.role)
            if idx >= 0:
                role_combo.setCurrentIndex(idx)
            idx = status_combo.findData(user.status)
            if idx >= 0:
                status_combo.setCurrentIndex(idx)

        layout.addLayout(form)

        btn_ok = QPushButton("确定")
        apply_css_class(btn_ok, "success")
        btn_cancel = QPushButton("取消")
        apply_css_class(btn_cancel, "secondary")
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        layout.addLayout(row)

        def accept():
            result = {
                "username": username_edit.text().strip(),
                "real_name": real_name_edit.text().strip(),
                "role": role_combo.currentData(),
                "status": status_combo.currentData(),
                "password": pwd_edit.text(),
            }
            dialog.result = result
            dialog.accept()

        btn_ok.clicked.connect(accept)
        btn_cancel.clicked.connect(dialog.reject)
        return dialog

    # ===== 页面回调 =====

    def refresh(self):
        self._load_data()

    def on_show(self):
        self._load_data()
