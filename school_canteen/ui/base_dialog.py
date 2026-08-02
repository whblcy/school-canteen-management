"""
对话框基类 - 所有业务对话框的统一父类
提供统一样式、消息框工具方法、表单布局辅助方法
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QMessageBox, QLabel, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from .style_helper import apply_css_class
from ..config import get_config

cfg = get_config()
ui = cfg.ui


class BaseDialog(QDialog):
    """对话框基类"""

    def __init__(self, parent=None, title: str = "", width: int = ui.base_dialog_width):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(width)
        # 显式设置窗口图标：保证登录框等所有对话框在任务栏/标题栏正确显示图标
        try:
            icon_file = str(cfg.paths.icon_file)
            if os.path.exists(icon_file):
                self.setWindowIcon(QIcon(icon_file))
        except Exception:
            pass
        self._setup_base()

    def _setup_base(self):
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(ui.operation_spacing)

    # ===== 消息框工具 =====

    def show_error(self, message: str, title: str = "错误"):
        QMessageBox.critical(self, title, message)

    def show_warning(self, message: str, title: str = "警告"):
        QMessageBox.warning(self, title, message)

    def show_info(self, message: str, title: str = "提示"):
        QMessageBox.information(self, title, message)

    def confirm(self, message: str, title: str = "确认") -> bool:
        """确认对话框，返回用户是否点击了'是'"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def confirm_with_input(self, message: str, expected: str,
                            title: str = "危险操作确认") -> bool:
        """
        二次确认：警告对话框 + 手动输入指定文字
        用于数据删除等不可逆操作
        """
        from PyQt6.QtWidgets import QLineEdit, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)

        warn_label = QLabel(f"<p style='color:{ui.color_red}; font-weight:bold;'>⚠ {message}</p>")
        warn_label.setWordWrap(True)
        layout.addWidget(warn_label)

        hint = QLabel(f"请输入 <b>{expected}</b> 以确认操作：")
        layout.addWidget(hint)

        input_field = QLineEdit()
        input_field.setMinimumWidth(ui.form_field_min_width)
        layout.addWidget(input_field)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("确认删除")

        def on_text_changed(text):
            btns.button(QDialogButtonBox.StandardButton.Ok).setEnabled(text == expected)
        input_field.textChanged.connect(on_text_changed)

        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        return dlg.exec() == QDialog.DialogCode.Accepted

    # ===== 表单布局辅助 =====

    def setup_form_field(self, field: QWidget, min_width: int = ui.form_field_min_width):
        """设置表单字段最小宽度"""
        field.setMinimumWidth(min_width)
        return field

    def create_button_layout(self, *buttons: QPushButton,
                              align_right: bool = True) -> QHBoxLayout:
        """创建按钮布局，右对齐"""
        layout = QHBoxLayout()
        layout.setSpacing(ui.button_spacing)
        if align_right:
            layout.addStretch()
        for btn in buttons:
            btn.setMinimumWidth(ui.button_min_width)
            layout.addWidget(btn)
        return layout

    def make_button(self, text: str, css_class: str = None,
                     min_width: int = ui.button_min_width) -> QPushButton:
        """创建带样式的按钮"""
        btn = QPushButton(text)
        btn.setMinimumWidth(min_width)
        if css_class:
            apply_css_class(btn, css_class)
        return btn
