"""
全局样式表 - macOS 风格设计系统
所有按钮和控件统一使用此样式，保证视觉一致性
"""
from ..config import get_config

cfg = get_config()
ui = cfg.ui


MAIN_STYLE = f"""
QWidget {{
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial;
    font-size: 14px;
    color: {ui.color_text};
}}

QMainWindow {{
    background: {ui.color_bg};
}}

/* 按钮 - 全局默认：白底+浅边框，在白色页面背景上也能清晰可见 */
QPushButton {{
    background: #ffffff;
    color: {ui.color_text};
    border: 1px solid #c8c8cc;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-width: 80px;
}}

QPushButton:hover {{
    background: #f5f5f7;
}}

QPushButton:pressed {{
    background: #e8e8ed;
}}

/* 主操作按钮（蓝底白字） */
QPushButton[cssClass="primary"] {{
    background: {ui.color_blue};
    color: white;
}}
QPushButton[cssClass="primary"]:hover {{
    background: {ui.color_blue_hover};
}}
QPushButton[cssClass="primary"]:pressed {{
    background: #0058b0;
}}

QPushButton:disabled {{
    background: #e5e5ea;
    color: #8a8a8f;
}}

/* 次要按钮 */
QPushButton[cssClass="secondary"] {{
    background: {ui.color_light_gray};
    color: {ui.color_text};
}}
QPushButton[cssClass="secondary"]:hover {{
    background: #e8e8ed;
}}

/* 危险按钮 */
QPushButton[cssClass="danger"] {{
    background: {ui.color_red};
    color: white;
}}
QPushButton[cssClass="danger"]:hover {{
    background: #ff5147;
}}

/* 成功按钮 */
QPushButton[cssClass="success"] {{
    background: {ui.color_green};
    color: {ui.color_text};
}}
QPushButton[cssClass="success"]:hover {{
    background: #2db84e;
}}

/* 警告按钮 */
QPushButton[cssClass="warning"] {{
    background: {ui.color_orange};
    color: {ui.color_text};
}}
QPushButton[cssClass="warning"]:hover {{
    background: #e68600;
}}

/* 输入控件 */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
    border: 1px solid {ui.color_border};
    border-radius: 6px;
    padding: 6px 10px;
    background: white;
    selection-background-color: {ui.color_blue};
    selection-color: white;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {ui.color_blue};
    padding: 5px 9px;
}}

/* 表格 */
QTableWidget {{
    border: 1px solid {ui.color_border};
    border-radius: 6px;
    background: white;
    alternate-background-color: #f6f6f9;
    gridline-color: {ui.color_border};
    selection-background-color: rgba(0, 113, 227, 0.12);
    selection-color: {ui.color_text};
}}

QHeaderView::section {{
    background: {ui.color_light_gray};
    color: {ui.color_text};
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {ui.color_border};
    border-right: 1px solid {ui.color_border};
}}

QTableWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {ui.color_border};
}}

/* 导航栏 */
QListWidget#navList {{
    background: #2c2c2e;
    color: #e5e5e7;
    border: none;
    border-right: 1px solid #3a3a3c;
    outline: none;
    font-size: 14px;
}}

QListWidget#navList::item {{
    padding: 14px 20px;
    border-bottom: 1px solid #3a3a3c;
}}

QListWidget#navList::item:hover {{
    background: #3a3a3c;
}}

QListWidget#navList::item:selected {{
    background: {ui.color_blue};
    color: white;
    border-left: 3px solid {ui.color_blue};
}}

/* 滚动条 */
QScrollBar:vertical {{
    border: none;
    background: {ui.color_light_gray};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {ui.color_border};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ui.color_gray};
}}

/* 标签 */
QLabel#titleLabel {{
    font-size: 24px;
    font-weight: 700;
    color: {ui.color_text};
    padding: 10px 0;
}}

QLabel#sectionLabel {{
    font-size: 16px;
    font-weight: 600;
    color: {ui.color_text};
    padding: 8px 0;
}}

/* 统计卡片 */
QFrame#statCard {{
    background: white;
    border: 1px solid {ui.color_border};
    border-radius: 10px;
    padding: 0;
}}

QLabel#statValue {{
    font-size: 28px;
    font-weight: 700;
    color: {ui.color_text};
}}

QLabel#statLabel {{
    font-size: 13px;
    color: {ui.color_text_secondary};
}}

/* 对话框 */
QDialog {{
    background: white;
}}

/* 分组框 */
QGroupBox {{
    border: 1px solid {ui.color_border};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}

/* Tab */
QTabWidget::pane {{
    border: 1px solid {ui.color_border};
    border-radius: 6px;
    background: white;
}}
QTabBar::tab {{
    background: {ui.color_light_gray};
    color: {ui.color_text};
    padding: 8px 16px;
    border: 1px solid {ui.color_border};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{
    background: white;
    color: {ui.color_blue};
    font-weight: 600;
}}

/* 进度条 */
QProgressBar {{
    border: 1px solid {ui.color_border};
    border-radius: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {ui.color_blue};
    border-radius: 4px;
}}
"""
