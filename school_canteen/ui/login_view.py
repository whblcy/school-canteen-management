"""
登录对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QHBoxLayout,
)
from PyQt6.QtCore import Qt
from .base_dialog import BaseDialog
from ..config import get_config
from .styles import MAIN_STYLE

cfg = get_config()
ui = cfg.ui


class LoginDialog(BaseDialog):
    """登录对话框"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent, "登录", 380)
        self.auth_service = auth_service
        self.current_user = None
        self._setup_ui()

    def _setup_ui(self):
        # 标题
        title = QLabel(cfg.app_name)
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ui.color_blue};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)

        subtitle = QLabel("请登录以继续")
        subtitle.setStyleSheet(f"font-size: 13px; color: {ui.color_text_secondary};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(subtitle)

        # 表单
        form = QFormLayout()
        form.setSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.setup_form_field(self.username_input, 250)
        form.addRow("用户名:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.setup_form_field(self.password_input, 250)
        form.addRow("密码:", self.password_input)

        self.content_layout.addLayout(form)

        # 按钮
        login_btn = self.make_button("登录")
        login_btn.clicked.connect(self._on_login)
        self.content_layout.addLayout(
            self.create_button_layout(login_btn))

        # 回车触发登录
        self.password_input.returnPressed.connect(self._on_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.show_warning("请输入用户名和密码")
            return

        try:
            user = self.auth_service.login(username, password)
            self.current_user = user
            self.accept()
        except Exception as e:
            self.show_error(f"登录失败:\n{str(e)}")
            self.password_input.clear()
