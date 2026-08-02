"""
页面基类 - 所有业务页面的统一父类
提供统一的页面标题、内容区布局、刷新接口
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from ..config import get_config

cfg = get_config()
ui = cfg.ui


class BasePage(QWidget):
    """业务页面基类"""

    # 数据变更信号，通知主窗口刷新相关页面
    data_changed = pyqtSignal(str)

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._setup_page()

    def _setup_page(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(24, 16, 24, 16)
        self.content_layout.setSpacing(ui.operation_spacing)

        if self._title_text:
            title_label = QLabel(self._title_text)
            title_label.setObjectName("titleLabel")
            self.content_layout.addWidget(title_label)

        scroll.setWidget(self.content)
        outer.addWidget(scroll)

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def refresh(self):
        """子类实现：刷新页面数据"""
        pass

    def on_show(self):
        """子类实现：页面被切换显示时的回调"""
        pass
