"""
Qt 样式工具函数

解决 PyQt6 按钮样式在 Windows 真机上不生效的问题。

背景：全局 QSS 的属性选择器（QPushButton[cssClass="primary"]）在某些
平台/Qt 版本下匹配不稳定，即使 setProperty + unpolish/polish 也无法保证。
实例级 setStyleSheet 是 Qt 样式优先级最高的方式，与全局样式表、选择器
匹配、unpolish/polish 全部无关，100% 生效。

因此对 QPushButton 直接写死完整实例样式（背景/hover/pressed/disabled），
其余控件类型仍走全局 QSS 的 cssClass 属性选择器。
"""
from PyQt6.QtWidgets import QWidget, QPushButton

# 各按钮类型完整实例样式（与 ui/styles.py 视觉一致）
_PRIMARY_QSS = """
QPushButton {
    background: #0066cc;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-width: 80px;
}
QPushButton:hover { background: #0077ee; }
QPushButton:pressed { background: #0058b0; }
QPushButton:disabled { background: #e5e5ea; color: #8a8a8f; }
"""

_SUCCESS_QSS = """
QPushButton {
    background: #34c759;
    color: #1d1d1f;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-width: 80px;
}
QPushButton:hover { background: #2db84e; }
QPushButton:pressed { background: #27a344; }
QPushButton:disabled { background: #e5e5ea; color: #8a8a8f; }
"""

_DANGER_QSS = """
QPushButton {
    background: #ff3b30;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-width: 80px;
}
QPushButton:hover { background: #ff5147; }
QPushButton:pressed { background: #e02b20; }
QPushButton:disabled { background: #e5e5ea; color: #8a8a8f; }
"""

_WARNING_QSS = """
QPushButton {
    background: #ff9500;
    color: #1d1d1f;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-width: 80px;
}
QPushButton:hover { background: #e68600; }
QPushButton:pressed { background: #d47a00; }
QPushButton:disabled { background: #e5e5ea; color: #8a8a8f; }
"""

_SECONDARY_QSS = """
QPushButton {
    background: #ffffff;
    color: #1d1d1f;
    border: 1px solid #c8c8cc;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-width: 80px;
}
QPushButton:hover { background: #f5f5f7; }
QPushButton:pressed { background: #e8e8ed; }
QPushButton:disabled { background: #f5f5f7; color: #8a8a8f; border-color: #e5e5ea; }
"""

_BUTTON_QSS = {
    "primary": _PRIMARY_QSS,
    "success": _SUCCESS_QSS,
    "danger": _DANGER_QSS,
    "warning": _WARNING_QSS,
    "secondary": _SECONDARY_QSS,
}


def apply_css_class(widget: QWidget, class_name: str) -> None:
    """给控件应用样式类。

    - QPushButton：直接写实例级 QSS（最高优先级，保证在真机生效）
    - 其他控件：设置 cssClass 属性 + unpolish/polish（走全局 QSS 选择器）

    用法::
        apply_css_class(btn, "primary")
        apply_css_class(btn, "success")
        apply_css_class(btn, "danger")
    """
    if isinstance(widget, QPushButton) and class_name in _BUTTON_QSS:
        widget.setStyleSheet(_BUTTON_QSS[class_name])
        return

    widget.setProperty("cssClass", class_name)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()
