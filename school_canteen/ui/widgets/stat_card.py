"""
统计卡片组件 - 用于概览页和统计页
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class StatCard(QFrame):
    """统计卡片 - 显示标题和数值"""

    def __init__(self, title: str, value: str = "0", color: str = None,
                 parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setFixedHeight(100)
        self._color = color or ui.color_text

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("statValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.value_label.setStyleSheet(f"color: {self._color};")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("statLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def set_value(self, value):
        self.value_label.setText(str(value))

    def set_color(self, color: str):
        self._color = color
        self.value_label.setStyleSheet(f"color: {color};")


class StatCardRow(QFrame):
    """统计卡片行 - 横向排列多个卡片"""

    def __init__(self, cards: list = None, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QHBoxLayout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        for card in (cards or []):
            layout.addWidget(card)
        layout.addStretch()
