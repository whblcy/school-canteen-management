"""
学校食堂食材管理系统 - 完整版主程序
功能: 食材管理、入库出库、库存盘点、财务统计、提醒中心、用户管理、数据备份
"""
import sys
import os
import shutil
import logging
import traceback
from datetime import datetime, date

# 获取程序运行目录（支持PyInstaller打包后的路径）
def get_resource_path(relative_path):
    """获取资源文件绝对路径，兼容开发环境和PyInstaller打包环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# 配置运行日志
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"canteen_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CanteenApp')
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTableWidget, 
                             QTableWidgetItem, QDialog, QLineEdit, QComboBox,
                             QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                             QHeaderView, QTabWidget, QFormLayout, QDateEdit,
                             QGroupBox, QFrame, QStackedWidget,
                             QFileDialog, QInputDialog, QGridLayout,
                             QScrollArea, QSizePolicy, QCheckBox)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor

from database import (init_database, DB_PATH, UserDAO, CategoryDAO, SupplierDAO, IngredientDAO,
                      StockInDAO, StockOutDAO, InventoryCheckDAO, ReportDAO, LogDAO,
                      InspectionRecordDAO, CategoryMappingDAO, InspectorDAO, get_connection)
from excel_handler import ExcelHandler
from report_generator import ReportGenerator


class StyleSheet:
    """macOS 风格样式表"""
    MAIN_STYLE = """
        QMainWindow {
            background-color: #f5f5f7;
        }
        QWidget {
            font-family: -apple-system, "SF Pro Display", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
            font-size: 13px;
            color: #1d1d1f;
        }
        QPushButton {
            background-color: #0071e3;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #0077ed;
        }
        QPushButton:pressed {
            background-color: #005bb5;
        }
        QPushButton#danger {
            background-color: #ff3b30;
        }
        QPushButton#danger:hover {
            background-color: #ff453a;
        }
        QPushButton#success {
            background-color: #34c759;
        }
        QPushButton#success:hover {
            background-color: #30d158;
        }
        QPushButton#warning {
            background-color: #ff9500;
        }
        QPushButton#warning:hover {
            background-color: #ff9f0a;
        }
        QPushButton#secondary {
            background-color: #e3e3e8;
            color: #1d1d1f;
        }
        QPushButton#secondary:hover {
            background-color: #d1d1d6;
        }
        QTableWidget {
            background-color: white;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            gridline-color: #f0f0f0;
            outline: none;
            alternate-background-color: #f8f9fa;
        }
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        QTableWidget::item:selected {
            background-color: #0071e3;
            color: white;
            border-radius: 4px;
        }
        QHeaderView::section {
            background-color: #f5f5f7;
            color: #1d1d1f;
            padding: 10px 8px;
            font-weight: 600;
            font-size: 12px;
            border: none;
            border-bottom: 1px solid #d2d2d7;
        }
        QTableView {
            background-color: white;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            gridline-color: #f0f0f0;
            outline: none;
            alternate-background-color: #f8f9fa;
        }
        QTableView::item {
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #0071e3;
        }
        QComboBox {
            border: 1px solid #d2d2d7;
            border-radius: 6px;
            padding: 6px 8px;
            background-color: white;
            min-height: 28px;
        }
        QComboBox::drop-down {
            border: none;
            border-left: 1px solid #d2d2d7;
            width: 28px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background-color: #f5f5f7;
        }
        QComboBox::drop-down:hover {
            background-color: #e3e3e8;
        }
        QComboBox::down-arrow {
            width: 8px;
            height: 8px;
            border-width: 0 0 2px 2px;
            border-style: solid;
            border-color: #86868b;
            transform: rotate(-45deg);
            margin-right: 8px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid #d2d2d7;
            border-radius: 8px;
            background-color: white;
            selection-background-color: #0071e3;
        }
        QGroupBox {
            font-weight: 600;
            border: 1px solid #d2d2d7;
            border-radius: 12px;
            margin-top: 12px;
            padding-top: 16px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: #1d1d1f;
            font-size: 14px;
        }
        QLabel#title {
            font-size: 22px;
            font-weight: 700;
            color: #1d1d1f;
        }
        QLabel#subtitle {
            font-size: 15px;
            color: #86868b;
        }
        QLabel#stat_number {
            font-size: 28px;
            font-weight: 700;
            color: #0071e3;
        }
        QLabel#stat_label {
            font-size: 13px;
            color: #86868b;
        }
        QTabWidget::pane {
            border: 1px solid #d2d2d7;
            background-color: white;
            border-radius: 12px;
            margin-top: -1px;
        }
        QTabBar::tab {
            background-color: transparent;
            padding: 10px 20px;
            margin-right: 4px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-weight: 500;
            color: #86868b;
        }
        QTabBar::tab:selected {
            background-color: white;
            color: #0071e3;
            border: 1px solid #d2d2d7;
            border-bottom: none;
        }
        QTabBar::tab:hover {
            background-color: #f5f5f7;
            color: #1d1d1f;
        }
        QScrollBar:vertical {
            background-color: transparent;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background-color: #c1c1c6;
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #a1a1a6;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QMessageBox {
            background-color: white;
        }
        QDialog {
            background-color: #f5f5f7;
        }
        QCalendarWidget {
            background-color: white;
            border: 1px solid #d2d2d7;
            border-radius: 8px;
        }
        QCalendarWidget QToolButton {
            background-color: #f5f5f7;
            color: #1d1d1f;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            min-width: 24px;
            min-height: 24px;
        }
        QCalendarWidget QToolButton:hover {
            background-color: #e3e3e8;
        }
        QCalendarWidget QMenu {
            background-color: white;
            border: 1px solid #d2d2d7;
            border-radius: 6px;
        }
        QCalendarWidget QWidget#qt_calendar_navigationbar {
            background-color: #f5f5f7;
            border: none;
            border-bottom: 1px solid #d2d2d7;
        }
        QCalendarWidget QAbstractItemView {
            background-color: white;
            selection-background-color: #0071e3;
            selection-color: white;
            border: none;
            outline: none;
        }
        QCalendarWidget QAbstractItemView::item {
            padding: 0px;
            border: none;
            min-width: 32px;
            min-height: 32px;
        }
    """


class BaseDialog(QDialog):
    """基础对话框"""
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)

    def show_error(self, message):
        QMessageBox.critical(self, "错误", message)

    def show_warning(self, message, title="提示"):
        QMessageBox.warning(self, title, message)

    def show_info(self, message):
        QMessageBox.information(self, "提示", message)

    def confirm(self, message):
        reply = QMessageBox.question(self, "确认", message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    @staticmethod
    def setup_form_field(widget, min_width=200):
        """设置表单输入控件的统一最小宽度"""
        widget.setMinimumWidth(min_width)
        return widget

    @staticmethod
    def create_button_layout(*buttons, align="right"):
        """创建统一的按钮布局，align: right/center/left"""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        if align == "right":
            layout.addStretch()
        elif align == "center":
            layout.addStretch()
        for btn in buttons:
            layout.addWidget(btn)
        if align == "center":
            layout.addStretch()
        return layout


class LoginDialog(QDialog):
    """登录对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录 - 学校食堂食材管理系统")
        self.setFixedSize(400, 420)
        self.current_user = None
        
        # 使用兼容路径获取图标
        self.icon_path = get_resource_path('app_icon.ico')
        logger.info(f"登录对话框图标路径: {self.icon_path}, 存在: {os.path.exists(self.icon_path)}")
        
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))
        
        self.setup_ui()
        logger.info("登录对话框初始化完成")
        
    def setup_ui(self):
        # 独立样式，不受全局样式影响
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 30)
        main_layout.setSpacing(0)
        
        # === 顶部 Logo 区域 ===
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(64, 64)
        self.logo_label.setScaledContents(True)
        self.logo_label.setStyleSheet("border: none; background: transparent;")
        
        if os.path.exists(self.icon_path):
            pixmap = QIcon(self.icon_path).pixmap(64, 64)
            self.logo_label.setPixmap(pixmap)
            logger.info("登录Logo图标已加载")
        else:
            self.logo_label.setText("LOGO")
            self.logo_label.setStyleSheet("""
                border: 2px dashed #d2d2d7;
                border-radius: 12px;
                color: #86868b;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            """)
            self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logger.warning("登录Logo图标未找到")
        
        logo_layout.addWidget(self.logo_label)
        logo_layout.addStretch()
        main_layout.addLayout(logo_layout)
        main_layout.addSpacing(16)
        
        # === 标题区域 ===
        title = QLabel("学校食堂食材管理系统")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1d1d1f; border: none; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel("请输入账号密码登录系统")
        subtitle.setStyleSheet("font-size: 13px; color: #86868b; border: none; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(28)
        
        # === 表单区域 ===
        # 用户名标签
        username_label = QLabel("用户名")
        username_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #1d1d1f; border: none; background: transparent;")
        main_layout.addWidget(username_label)
        main_layout.addSpacing(4)
        
        # 用户名输入框
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setFixedHeight(40)
        self.username_edit.setStyleSheet("""
            QLineEdit {
                padding: 0 12px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
            }
        """)
        main_layout.addWidget(self.username_edit)
        main_layout.addSpacing(14)
        
        # 密码标签
        password_label = QLabel("密码")
        password_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #1d1d1f; border: none; background: transparent;")
        main_layout.addWidget(password_label)
        main_layout.addSpacing(4)
        
        # 密码输入框
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setFixedHeight(40)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                padding: 0 12px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
            }
        """)
        main_layout.addWidget(self.password_edit)
        
        main_layout.addSpacing(24)
        
        # === 登录按钮 ===
        self.btn_login = QPushButton("登 录")
        self.btn_login.setFixedHeight(42)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #0077ed;
            }
            QPushButton:pressed {
                background-color: #005bb5;
            }
        """)
        self.btn_login.clicked.connect(self.do_login)
        main_layout.addWidget(self.btn_login)
        
        main_layout.addSpacing(16)
        
        # === 提示信息 ===
        hint = QLabel("默认账号: admin   密码: admin123")
        hint.setStyleSheet("font-size: 12px; color: #86868b; border: none; background: transparent;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(hint)
        
        main_layout.addStretch()
        
    def do_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return
        
        logger.info(f"用户尝试登录: {username}")
        user = UserDAO.authenticate(username, password)
        if user:
            self.current_user = user
            logger.info(f"用户登录成功: {username} (ID={user.id}, role={user.role})")
            self.accept()
        else:
            logger.warning(f"用户登录失败: {username}")
            QMessageBox.critical(self, "登录失败", "用户名或密码错误")
            self.password_edit.clear()


class CategoryDialog(BaseDialog):
    """分类管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "食材分类管理")
        self.setMinimumWidth(600)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "分类名称", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加分类")
        self.btn_add.setObjectName("success")
        self.btn_edit = QPushButton("编辑")
        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("danger")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.btn_add.clicked.connect(self.add_category)
        self.btn_edit.clicked.connect(self.edit_category)
        self.btn_delete.clicked.connect(self.delete_category)
        
    def load_data(self):
        categories = CategoryDAO.get_all()
        self.table.setRowCount(len(categories))
        for i, cat in enumerate(categories):
            self.table.setItem(i, 0, QTableWidgetItem(str(cat.id)))
            self.table.setItem(i, 1, QTableWidgetItem(cat.name))
            self.table.setItem(i, 2, QTableWidgetItem(cat.description))
    
    def add_category(self):
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称:")
        if ok and name:
            desc, _ = QInputDialog.getText(self, "添加分类", "描述:")
            if CategoryDAO.add(name, desc):
                self.show_info("添加成功")
                LogDAO.add(None, "添加分类", "category", 0, f"分类名称: {name}")
                self.load_data()
            else:
                self.show_error("分类名称已存在")
    
    def edit_category(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要编辑的分类")
            return
        
        cat_id = int(self.table.item(row, 0).text())
        old_name = self.table.item(row, 1).text()
        old_desc = self.table.item(row, 2).text()
        
        name, ok = QInputDialog.getText(self, "编辑分类", "分类名称:", text=old_name)
        if ok and name:
            desc, _ = QInputDialog.getText(self, "编辑分类", "描述:", text=old_desc)
            if CategoryDAO.update(cat_id, name, desc):
                self.show_info("更新成功")
                LogDAO.add(None, "编辑分类", "category", cat_id, f"新名称: {name}")
                self.load_data()
            else:
                self.show_error("更新失败")
    
    def delete_category(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要删除的分类")
            return
        
        cat_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        
        if self.confirm(f"确定要删除分类 '{name}' 吗？"):
            if CategoryDAO.delete(cat_id):
                self.show_info("删除成功")
                LogDAO.add(None, "删除分类", "category", cat_id, f"分类名称: {name}")
                self.load_data()
            else:
                self.show_error("删除失败，该分类可能已被使用")


class CategoryMappingDialog(BaseDialog):
    """类别映射管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "类别映射管理")
        self.setMinimumWidth(700)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "外部类别", "系统分类", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加映射")
        self.btn_add.setObjectName("success")
        self.btn_edit = QPushButton("编辑")
        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("danger")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.btn_add.clicked.connect(self.add_mapping)
        self.btn_edit.clicked.connect(self.edit_mapping)
        self.btn_delete.clicked.connect(self.delete_mapping)
        
    def load_data(self):
        mappings = CategoryMappingDAO.get_all()
        self.table.setRowCount(len(mappings))
        for i, m in enumerate(mappings):
            self.table.setItem(i, 0, QTableWidgetItem(str(m.id)))
            self.table.setItem(i, 1, QTableWidgetItem(m.source_category))
            self.table.setItem(i, 2, QTableWidgetItem(m.target_category_name))
            self.table.setItem(i, 3, QTableWidgetItem(m.description))
    
    def add_mapping(self):
        dialog = CategoryMappingEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if CategoryMappingDAO.add(**data):
                self.show_info("添加成功")
                LogDAO.add(None, "添加类别映射", "category_mapping", 0, 
                           f"{data['source_category']} -> {data['target_category_id']}")
                self.load_data()
            else:
                self.show_error("添加失败，该外部类别已存在")
    
    def edit_mapping(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要编辑的映射")
            return
        
        mapping_id = int(self.table.item(row, 0).text())
        dialog = CategoryMappingEditDialog(self, mapping_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if CategoryMappingDAO.update(mapping_id, **data):
                self.show_info("更新成功")
                LogDAO.add(None, "编辑类别映射", "category_mapping", mapping_id, 
                           f"{data['source_category']} -> {data['target_category_id']}")
                self.load_data()
            else:
                self.show_error("更新失败，该外部类别已存在")
    
    def delete_mapping(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要删除的映射")
            return
        
        mapping_id = int(self.table.item(row, 0).text())
        source = self.table.item(row, 1).text()
        
        if self.confirm(f"确定要删除映射 '{source}' 吗？"):
            if CategoryMappingDAO.delete(mapping_id):
                self.show_info("删除成功")
                LogDAO.add(None, "删除类别映射", "category_mapping", mapping_id, f"外部类别: {source}")
                self.load_data()
            else:
                self.show_error("删除失败，记录可能不存在或已被删除")


class CategoryMappingEditDialog(BaseDialog):
    """类别映射编辑对话框"""
    def __init__(self, parent=None, mapping_id=None):
        super().__init__(parent, "编辑类别映射" if mapping_id else "添加类别映射")
        self.mapping_id = mapping_id
        self.setup_ui()
        if mapping_id:
            self.load_data()

    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("外部系统中的类别名称")

        self.target_combo = QComboBox()
        self.load_categories()

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("备注说明")
        for w in [self.source_edit, self.target_combo, self.desc_edit]:
            w.setMinimumWidth(250)

        layout.addRow("外部类别名称*:", self.source_edit)
        layout.addRow("映射到系统分类*:", self.target_combo)
        layout.addRow("备注:", self.desc_edit)

        self.btn_save = QPushButton("保存")
        self.btn_save.setObjectName("success")
        self.btn_save.setMinimumWidth(80)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setMinimumWidth(80)
        btn_layout = self.create_button_layout(self.btn_save, self.btn_cancel)
        layout.addRow("", btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
    
    def load_categories(self):
        self.target_combo.clear()
        categories = CategoryDAO.get_all()
        for cat in categories:
            self.target_combo.addItem(cat.name, cat.id)
    
    def load_data(self):
        mappings = CategoryMappingDAO.get_all()
        for m in mappings:
            if m.id == self.mapping_id:
                self.source_edit.setText(m.source_category)
                idx = self.target_combo.findData(m.target_category_id)
                if idx >= 0:
                    self.target_combo.setCurrentIndex(idx)
                self.desc_edit.setText(m.description)
                break
    
    def get_data(self):
        return {
            'source_category': self.source_edit.text().strip(),
            'target_category_id': self.target_combo.currentData(),
            'description': self.desc_edit.text().strip()
        }


class SupplierDialog(BaseDialog):
    """供应商管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "供应商管理")
        self.setMinimumWidth(800)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 顶部操作区
        op_group = QGroupBox("操作区")
        op_layout = QVBoxLayout(op_group)
        op_layout.setSpacing(10)

        # 第一行：搜索和筛选
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索供应商名称、联系人、电话...")
        self.search_edit.returnPressed.connect(self.search)
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.search)
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.load_data)

        row1.addWidget(self.search_edit, 1)
        row1.addWidget(self.search_btn)
        row1.addWidget(self.btn_refresh)
        op_layout.addLayout(row1)

        # 第二行：操作按钮
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.btn_add = QPushButton("➕ 添加供应商")
        self.btn_add.setObjectName("success")
        self.btn_edit = QPushButton("✏️ 编辑")
        self.btn_delete = QPushButton("🗑️ 删除")
        self.btn_delete.setObjectName("danger")

        row2.addWidget(self.btn_add)
        row2.addWidget(self.btn_edit)
        row2.addWidget(self.btn_delete)
        row2.addStretch()
        op_layout.addLayout(row2)
        
        layout.addWidget(op_group)
        
        # 底部数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "供应商名称", "联系人", "电话", "地址", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)
        
        self.btn_add.clicked.connect(self.add_supplier)
        self.btn_edit.clicked.connect(self.edit_supplier)
        self.btn_delete.clicked.connect(self.delete_supplier)
        
    def load_data(self):
        suppliers = SupplierDAO.get_all()
        self.table.setRowCount(len(suppliers))
        for i, s in enumerate(suppliers):
            self.table.setItem(i, 0, QTableWidgetItem(str(s.id)))
            self.table.setItem(i, 1, QTableWidgetItem(s.name))
            self.table.setItem(i, 2, QTableWidgetItem(s.contact_person))
            self.table.setItem(i, 3, QTableWidgetItem(s.phone))
            self.table.setItem(i, 4, QTableWidgetItem(s.address))
            self.table.setItem(i, 5, QTableWidgetItem("正常" if s.status else "停用"))
    
    def search(self):
        keyword = self.search_edit.text().lower().strip()
        suppliers = SupplierDAO.get_all()
        if keyword:
            filtered = [s for s in suppliers if 
                       keyword in str(s.name).lower() or 
                       keyword in str(s.contact_person).lower() or 
                       keyword in str(s.phone).lower()]
        else:
            filtered = suppliers
        
        self.table.setRowCount(len(filtered))
        for i, s in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(str(s.id)))
            self.table.setItem(i, 1, QTableWidgetItem(s.name))
            self.table.setItem(i, 2, QTableWidgetItem(s.contact_person))
            self.table.setItem(i, 3, QTableWidgetItem(s.phone))
            self.table.setItem(i, 4, QTableWidgetItem(s.address))
            self.table.setItem(i, 5, QTableWidgetItem("正常" if s.status else "停用"))
    
    def add_supplier(self):
        dialog = SupplierEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                sid = SupplierDAO.add(**data)
                self.show_info("添加成功")
                LogDAO.add(None, "添加供应商", "supplier", sid, f"供应商: {data['name']}")
                self.load_data()
            except Exception as e:
                self.show_error(f"添加失败: {str(e)}")

    def edit_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要编辑的供应商")
            return

        supplier_id = int(self.table.item(row, 0).text())
        dialog = SupplierEditDialog(self, supplier_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                SupplierDAO.update(supplier_id, **data)
                self.show_info("更新成功")
                LogDAO.add(None, "编辑供应商", "supplier", supplier_id, f"供应商: {data['name']}")
                self.load_data()
            except Exception as e:
                self.show_error(f"更新失败: {str(e)}")
    
    def delete_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要删除的供应商")
            return
        
        supplier_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        
        if self.confirm(f"确定要删除供应商 '{name}' 吗？"):
            if SupplierDAO.delete(supplier_id):
                self.show_info("删除成功")
                LogDAO.add(None, "删除供应商", "supplier", supplier_id, f"供应商: {name}")
                self.load_data()
            else:
                self.show_error("删除失败，该供应商可能已被使用")


class SupplierEditDialog(BaseDialog):
    """供应商编辑对话框"""
    def __init__(self, parent=None, supplier_id=None):
        super().__init__(parent, "编辑供应商" if supplier_id else "添加供应商")
        self.supplier_id = supplier_id
        self.setup_ui()
        if supplier_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setMinimumWidth(250)
        self.contact_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.email_edit = QLineEdit()
        for w in [self.name_edit, self.contact_edit, self.phone_edit, self.address_edit, self.email_edit]:
            w.setMinimumWidth(250)

        layout.addRow("供应商名称*:", self.name_edit)
        layout.addRow("联系人:", self.contact_edit)
        layout.addRow("电话:", self.phone_edit)
        layout.addRow("地址:", self.address_edit)
        layout.addRow("邮箱:", self.email_edit)

        self.btn_save = QPushButton("保存")
        self.btn_save.setObjectName("success")
        self.btn_save.setMinimumWidth(80)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setMinimumWidth(80)
        btn_layout = self.create_button_layout(self.btn_save, self.btn_cancel)
        layout.addRow("", btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
    
    def load_data(self):
        suppliers = SupplierDAO.get_all()
        for s in suppliers:
            if s.id == self.supplier_id:
                self.name_edit.setText(s.name)
                self.contact_edit.setText(s.contact_person)
                self.phone_edit.setText(s.phone)
                self.address_edit.setText(s.address)
                self.email_edit.setText(s.email)
                break
    
    def get_data(self):
        return {
            'name': self.name_edit.text(),
            'contact_person': self.contact_edit.text(),
            'phone': self.phone_edit.text(),
            'address': self.address_edit.text(),
            'email': self.email_edit.text()
        }


class IngredientDialog(BaseDialog):
    """食材管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "食材管理")
        self.setMinimumWidth(900)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 顶部操作区
        op_group = QGroupBox("操作区")
        op_layout = QVBoxLayout(op_group)
        op_layout.setSpacing(10)

        # 第一行：搜索和筛选
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索食材名称、分类、供应商...")
        self.search_edit.returnPressed.connect(self.search)
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.search)
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.load_data)

        row1.addWidget(self.search_edit, 1)
        row1.addWidget(self.search_btn)
        row1.addWidget(self.btn_refresh)
        op_layout.addLayout(row1)

        # 第二行：操作按钮
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.btn_add = QPushButton("➕ 添加食材")
        self.btn_add.setObjectName("success")
        self.btn_edit = QPushButton("✏️ 编辑")
        self.btn_delete = QPushButton("🗑️ 删除")
        self.btn_delete.setObjectName("danger")
        self.btn_import = QPushButton("📥 导入Excel")
        self.btn_import.setObjectName("warning")
        self.btn_export = QPushButton("📤 导出余量")
        self.btn_export.setObjectName("success")
        self.btn_template = QPushButton("📄 下载模板")

        row2.addWidget(self.btn_add)
        row2.addWidget(self.btn_edit)
        row2.addWidget(self.btn_delete)
        row2.addStretch()
        row2.addWidget(self.btn_import)
        row2.addWidget(self.btn_export)
        row2.addWidget(self.btn_template)
        op_layout.addLayout(row2)
        
        layout.addWidget(op_group)
        
        # 底部数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材名称", "分类", "规格", "单位", "当前库存", "安全库存", "供应商"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)
        
        self.btn_add.clicked.connect(self.add_ingredient)
        self.btn_edit.clicked.connect(self.edit_ingredient)
        self.btn_delete.clicked.connect(self.delete_ingredient)
        self.btn_import.clicked.connect(self.import_excel)
        self.btn_export.clicked.connect(self.export_excel)
        self.btn_template.clicked.connect(self.download_template)
        
    def load_data(self):
        ingredients = IngredientDAO.get_all()
        self.table.setRowCount(len(ingredients))
        for i, ing in enumerate(ingredients):
            self.table.setItem(i, 0, QTableWidgetItem(str(ing.id)))
            self.table.setItem(i, 1, QTableWidgetItem(ing.name))
            self.table.setItem(i, 2, QTableWidgetItem(ing.category_name))
            self.table.setItem(i, 3, QTableWidgetItem(ing.specification))
            self.table.setItem(i, 4, QTableWidgetItem(ing.unit))
            self.table.setItem(i, 5, QTableWidgetItem(str(ing.current_stock)))
            self.table.setItem(i, 6, QTableWidgetItem(str(ing.safety_stock)))
            self.table.setItem(i, 7, QTableWidgetItem(ing.supplier_name))
            
            if ing.current_stock <= ing.safety_stock:
                self.table.item(i, 5).setBackground(QColor("#ffcccc"))
    
    def search(self):
        keyword = self.search_edit.text().lower()
        ingredients = IngredientDAO.get_all()
        filtered = [ing for ing in ingredients
                    if keyword in ing.name.lower()
                    or keyword in (ing.category_name or "").lower()
                    or keyword in (ing.supplier_name or "").lower()
                    or keyword in (ing.specification or "").lower()]

        self.table.setRowCount(len(filtered))
        for i, ing in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(str(ing.id)))
            self.table.setItem(i, 1, QTableWidgetItem(ing.name))
            self.table.setItem(i, 2, QTableWidgetItem(ing.category_name))
            self.table.setItem(i, 3, QTableWidgetItem(ing.specification))
            self.table.setItem(i, 4, QTableWidgetItem(ing.unit))
            self.table.setItem(i, 5, QTableWidgetItem(str(ing.current_stock)))
            self.table.setItem(i, 6, QTableWidgetItem(str(ing.safety_stock)))
            self.table.setItem(i, 7, QTableWidgetItem(ing.supplier_name))

            if ing.current_stock <= ing.safety_stock:
                self.table.item(i, 5).setBackground(QColor("#ffcccc"))
    
    def add_ingredient(self):
        dialog = IngredientEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                iid = IngredientDAO.add(**data)
                self.show_info("添加成功")
                LogDAO.add(None, "添加食材", "ingredient", iid, f"食材: {data['name']}")
                self.load_data()
            except Exception as e:
                self.show_error(f"添加失败: {str(e)}")

    def edit_ingredient(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要编辑的食材")
            return

        ingredient_id = int(self.table.item(row, 0).text())
        dialog = IngredientEditDialog(self, ingredient_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                IngredientDAO.update(ingredient_id, **data)
                self.show_info("更新成功")
                LogDAO.add(None, "编辑食材", "ingredient", ingredient_id, f"食材: {data['name']}")
                self.load_data()
            except Exception as e:
                self.show_error(f"更新失败: {str(e)}")
    
    def delete_ingredient(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要删除的食材")
            return
        
        ingredient_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        
        if self.confirm(f"确定要删除食材 '{name}' 吗？"):
            if IngredientDAO.delete(ingredient_id):
                self.show_info("删除成功")
                LogDAO.add(None, "删除食材", "ingredient", ingredient_id, f"食材: {name}")
                self.load_data()
            else:
                self.show_error("删除失败，该食材可能已被入库/出库记录引用，无法删除")
    
    def import_excel(self):
        success, msg = ExcelHandler.import_ingredients(self)
        if success:
            QMessageBox.information(self, "导入结果", msg)
            LogDAO.add(None, "Excel导入食材", "ingredient", 0, "批量导入")
            self.load_data()
        else:
            QMessageBox.warning(self, "导入失败", msg)
    
    def export_excel(self):
        if ExcelHandler.export_ingredients(self):
            QMessageBox.information(self, "导出成功", "食材余量信息已导出!")
            LogDAO.add(None, "Excel导出食材", "ingredient", 0, "导出余量")
    
    def download_template(self):
        if ExcelHandler.create_template(self):
            QMessageBox.information(self, "模板已创建", "导入模板已保存!")


class IngredientEditDialog(BaseDialog):
    """食材编辑对话框"""
    def __init__(self, parent=None, ingredient_id=None):
        super().__init__(parent, "编辑食材" if ingredient_id else "添加食材")
        self.ingredient_id = ingredient_id
        self.setup_ui()
        if ingredient_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.name_edit = QLineEdit()

        self.category_combo = QComboBox()
        categories = CategoryDAO.get_all()
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)

        self.unit_edit = QLineEdit()
        self.spec_edit = QLineEdit()
        self.safety_stock_spin = QDoubleSpinBox()
        self.safety_stock_spin.setMaximum(999999)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- 请选择 --", None)
        suppliers = SupplierDAO.get_active()
        for s in suppliers:
            self.supplier_combo.addItem(s.name, s.id)
        for w in [self.name_edit, self.category_combo, self.unit_edit, self.spec_edit, self.safety_stock_spin, self.supplier_combo]:
            w.setMinimumWidth(250)

        layout.addRow("食材名称*:", self.name_edit)
        layout.addRow("分类*:", self.category_combo)
        layout.addRow("单位*:", self.unit_edit)
        layout.addRow("规格:", self.spec_edit)
        layout.addRow("安全库存:", self.safety_stock_spin)
        layout.addRow("供应商:", self.supplier_combo)

        self.btn_save = QPushButton("保存")
        self.btn_save.setObjectName("success")
        self.btn_save.setMinimumWidth(80)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setMinimumWidth(80)
        btn_layout = self.create_button_layout(self.btn_save, self.btn_cancel)
        layout.addRow("", btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
    
    def load_data(self):
        ingredient = IngredientDAO.get_by_id(self.ingredient_id)
        if ingredient:
            self.name_edit.setText(ingredient.name)
            index = self.category_combo.findData(ingredient.category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            self.unit_edit.setText(ingredient.unit)
            self.spec_edit.setText(ingredient.specification)
            self.safety_stock_spin.setValue(ingredient.safety_stock)
            if ingredient.supplier_id:
                index = self.supplier_combo.findData(ingredient.supplier_id)
                if index >= 0:
                    self.supplier_combo.setCurrentIndex(index)
    
    def get_data(self):
        return {
            'name': self.name_edit.text(),
            'category_id': self.category_combo.currentData(),
            'unit': self.unit_edit.text(),
            'specification': self.spec_edit.text(),
            'safety_stock': self.safety_stock_spin.value(),
            'supplier_id': self.supplier_combo.currentData()
        }


class StockInDialog(BaseDialog):
    """入库管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "入库管理")
        self.setMinimumWidth(1000)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 顶部操作区 - 新增入库表单
        form_group = QGroupBox("新增入库")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 第一行：食材和数量
        row1 = QHBoxLayout()
        self.ingredient_combo = QComboBox()
        self.load_ingredients()
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setPrefix("数量: ")
        
        row1.addWidget(QLabel("食材*:"))
        row1.addWidget(self.ingredient_combo, 1)
        row1.addWidget(self.quantity_spin)
        form_layout.addRow(row1)
        
        # 第二行：单价、供应商、批次号
        row2 = QHBoxLayout()
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        self.price_spin.setPrefix("¥ ")
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- 请选择供应商 --", None)
        suppliers = SupplierDAO.get_active()
        for s in suppliers:
            self.supplier_combo.addItem(s.name, s.id)
        self.batch_edit = QLineEdit()
        self.batch_edit.setPlaceholderText("批次号")
        
        row2.addWidget(QLabel("单价*:"))
        row2.addWidget(self.price_spin)
        row2.addWidget(QLabel("供应商:"))
        row2.addWidget(self.supplier_combo, 1)
        row2.addWidget(QLabel("批次号:"))
        row2.addWidget(self.batch_edit)
        form_layout.addRow(row2)
        
        # 第三行：生产日期、保质期、操作人
        row3 = QHBoxLayout()
        self.production_date = QDateEdit()
        self.production_date.setCalendarPopup(True)
        self.production_date.setDate(QDate.currentDate())
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addDays(30))
        self.operator_edit = QLineEdit()
        self.operator_edit.setPlaceholderText("操作人")
        
        row3.addWidget(QLabel("生产日期:"))
        row3.addWidget(self.production_date)
        row3.addWidget(QLabel("保质期至:"))
        row3.addWidget(self.expiry_date)
        row3.addWidget(QLabel("操作人:"))
        row3.addWidget(self.operator_edit, 1)
        form_layout.addRow(row3)
        
        # 第四行：备注和按钮
        row4 = QHBoxLayout()
        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("备注")
        self.btn_in = QPushButton("✅ 确认入库")
        self.btn_in.setObjectName("success")
        self.btn_in.setMinimumWidth(120)
        
        row4.addWidget(QLabel("备注:"))
        row4.addWidget(self.remark_edit, 1)
        row4.addWidget(self.btn_in)
        form_layout.addRow(row4)
        
        layout.addWidget(form_group)
        
        # 中间筛选区
        filter_group = QGroupBox("筛选查询")
        filter_layout = QHBoxLayout(filter_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索食材名称、批次号、操作人...")
        self.search_edit.returnPressed.connect(self.search_records)
        self.btn_search = QPushButton("搜索")
        self.btn_search.clicked.connect(self.search_records)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.load_data)
        
        filter_layout.addWidget(QLabel("日期范围:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("至"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(self.search_edit, 1)
        filter_layout.addWidget(self.btn_search)
        filter_layout.addWidget(self.btn_refresh)
        layout.addWidget(filter_group)
        
        # 导入功能区
        import_group = QGroupBox("批量导入")
        import_layout = QHBoxLayout(import_group)
        
        import_tip = QLabel("📥 从销售订单Excel文件批量导入入库数据，自动创建食材档案和入库记录")
        import_tip.setStyleSheet("color: #86868b; font-size: 12px;")
        
        self.btn_import_sales = QPushButton("导入销售订单")
        self.btn_import_sales.setObjectName("success")
        self.btn_import_sales.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import_sales.clicked.connect(self.import_sales_order)
        
        import_layout.addWidget(import_tip, 1)
        import_layout.addWidget(self.btn_import_sales)
        layout.addWidget(import_group)
        
        # 底部数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材", "数量", "单价", "总价", "供应商", "操作人", "入库时间"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 160)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)
        
        self.btn_in.clicked.connect(self.do_stock_in)
        
    def load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = IngredientDAO.get_all()
        for ing in ingredients:
            self.ingredient_combo.addItem(f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id)
    
    def load_data(self):
        records = StockInDAO.get_all()
        self._populate_table(records)
    
    def _populate_table(self, records):
        suppliers = {s.id: s.name for s in SupplierDAO.get_all()}
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.id)))
            self.table.setItem(i, 1, QTableWidgetItem(r.ingredient_name))
            self.table.setItem(i, 2, QTableWidgetItem(str(r.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(f"¥{r.unit_price:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"¥{r.total_price:.2f}"))
            supplier_name = suppliers.get(r.supplier_id, "-") if r.supplier_id else "-"
            self.table.setItem(i, 5, QTableWidgetItem(supplier_name))
            self.table.setItem(i, 6, QTableWidgetItem(r.operator))
            self.table.setItem(i, 7, QTableWidgetItem(r.created_at[:19]))
    
    def search_records(self):
        keyword = self.search_edit.text().lower().strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        records = StockInDAO.get_all()
        filtered = []
        for r in records:
            # 日期筛选
            record_date = r.created_at[:10]
            if record_date < date_from or record_date > date_to:
                continue
            # 关键词筛选
            if keyword:
                if keyword not in str(r.ingredient_name).lower() and \
                   keyword not in str(r.batch_number).lower() and \
                   keyword not in str(r.operator).lower():
                    continue
            filtered.append(r)
        
        self._populate_table(filtered)
    
    def do_stock_in(self):
        ingredient_id = self.ingredient_combo.currentData()
        quantity = self.quantity_spin.value()
        price = self.price_spin.value()

        if not ingredient_id or quantity <= 0 or price < 0:
            self.show_error("请填写完整的入库信息")
            return

        try:
            StockInDAO.add(
                ingredient_id=ingredient_id,
                quantity=quantity,
                unit_price=price,
                supplier_id=self.supplier_combo.currentData(),
                batch_number=self.batch_edit.text(),
                production_date=self.production_date.date().toString("yyyy-MM-dd"),
                expiry_date=self.expiry_date.date().toString("yyyy-MM-dd"),
                operator=self.operator_edit.text(),
                remark=self.remark_edit.text()
            )

            self.show_info("入库成功")
            LogDAO.add(None, "入库", "stock_in", 0, f"食材ID: {ingredient_id}, 数量: {quantity}")
            self.load_data()
            self.load_ingredients()

            self.quantity_spin.setValue(1)
            self.price_spin.setValue(0)
            self.batch_edit.clear()
            self.remark_edit.clear()
        except ValueError as e:
            self.show_error(f"入库失败: {str(e)}")
        except Exception as e:
            self.show_error(f"入库操作异常: {str(e)}")
    
    def import_sales_order(self):
        """从销售订单导入入库数据"""
        success, msg = ExcelHandler.import_sales_orders(self)
        if success:
            self.show_info(msg)
            LogDAO.add(None, "导入销售订单", "import", 0, "从Excel导入销售订单数据")
            self.load_data()
            self.load_ingredients()
        else:
            self.show_error(msg)


class InspectionRecordDialog(BaseDialog):
    """进货查验记录管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "进货查验记录")
        self.setMinimumWidth(1100)
        self.setup_ui()
        self.load_inspectors()
        self.load_data()
        self.load_stockin_data()
    
    def _get_this_month_range(self):
        """获取本月的日期范围"""
        today = QDate.currentDate()
        first_day = QDate(today.year(), today.month(), 1)
        last_day = QDate(today.year(), today.month(), today.daysInMonth())
        return first_day, last_day
        
    def load_inspectors(self):
        """加载查验人员列表到下拉框"""
        inspectors = InspectorDAO.get_active()
        self.batch_inspector_combo.clear()
        if inspectors:
            self.batch_inspector_combo.addItems([i.name for i in inspectors])
        else:
            self.batch_inspector_combo.setPlaceholderText("请先在系统设置添加查验人员")
            self.batch_inspector_combo.addItem("请先添加查验人员")
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 顶部批量录入区域
        batch_group = QGroupBox("批量录入查验记录")
        batch_layout = QVBoxLayout(batch_group)
        batch_layout.setSpacing(10)
        
        # 第一行：加载选项
        load_row = QHBoxLayout()
        
        load_row.addWidget(QLabel("选择日期:"))
        self.load_date = QDateEdit()
        self.load_date.setCalendarPopup(True)
        self.load_date.setDate(QDate.currentDate())
        self.load_date.setMinimumWidth(120)
        load_row.addWidget(self.load_date)
        
        self.btn_load_stockin = QPushButton("📥 加载入库数据")
        self.btn_load_stockin.setObjectName("success")
        self.btn_load_stockin.clicked.connect(self.load_stockin_data)
        load_row.addWidget(self.btn_load_stockin)
        
        load_row.addSpacing(30)
        
        load_row.addWidget(QLabel("查验结果:"))
        self.batch_result_combo = QComboBox()
        self.batch_result_combo.addItems(["合格", "不合格", "待复检"])
        self.batch_result_combo.setFixedWidth(100)
        load_row.addWidget(self.batch_result_combo)
        
        load_row.addWidget(QLabel("查验人:"))
        self.batch_inspector_combo = QComboBox()
        self.batch_inspector_combo.setEditable(True)
        self.batch_inspector_combo.setMinimumWidth(150)
        load_row.addWidget(self.batch_inspector_combo)
        
        self.btn_batch_set = QPushButton("⚡ 批量设置")
        self.btn_batch_set.setObjectName("secondary")
        self.btn_batch_set.clicked.connect(self.batch_set_fields)
        load_row.addWidget(self.btn_batch_set)
        
        load_row.addStretch()
        batch_layout.addLayout(load_row)
        
        # 第二行：操作按钮
        btn_row = QHBoxLayout()
        
        self.btn_select_all = QPushButton("✅ 全选")
        self.btn_select_all.setObjectName("secondary")
        self.btn_select_all.clicked.connect(self.select_all_batch)
        
        self.btn_unselect_all = QPushButton("❌ 取消全选")
        self.btn_unselect_all.setObjectName("secondary")
        self.btn_unselect_all.clicked.connect(self.unselect_all_batch)
        
        self.btn_delete_selected = QPushButton("🗑️ 删除选中行")
        self.btn_delete_selected.setObjectName("danger")
        self.btn_delete_selected.clicked.connect(self.delete_selected_batch_rows)
        
        self.btn_clear = QPushButton("🧹 清空表格")
        self.btn_clear.setObjectName("secondary")
        self.btn_clear.clicked.connect(self.clear_batch_table)
        
        btn_row.addWidget(self.btn_select_all)
        btn_row.addWidget(self.btn_unselect_all)
        btn_row.addWidget(self.btn_delete_selected)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch()
        
        self.btn_batch_save = QPushButton("💾 批量保存查验记录")
        self.btn_batch_save.setObjectName("success")
        self.btn_batch_save.setMinimumWidth(160)
        self.btn_batch_save.clicked.connect(self.batch_save)
        btn_row.addWidget(self.btn_batch_save)
        
        batch_layout.addLayout(btn_row)
        
        # 批量编辑表格
        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(13)
        self.batch_table.setHorizontalHeaderLabels([
            "✅", "食材", "数量", "单位", "生产日期", "保质期", 
            "供应商", "批号", "查验结果", "查验人", "备注", "ingredient_id", "stock_in_id"
        ])
        self.batch_table.setColumnHidden(11, True)
        self.batch_table.setColumnHidden(12, True)
        self.batch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.batch_table.horizontalHeader().setSectionsMovable(True)
        self.batch_table.horizontalHeader().setHighlightSections(False)
        self.batch_table.verticalHeader().setDefaultSectionSize(32)
        # 设置默认列宽
        self.batch_table.setColumnWidth(0, 40)   # ✅
        self.batch_table.setColumnWidth(1, 120)  # 食材
        self.batch_table.setColumnWidth(2, 80)   # 数量
        self.batch_table.setColumnWidth(3, 60)   # 单位
        self.batch_table.setColumnWidth(4, 100)  # 生产日期
        self.batch_table.setColumnWidth(5, 80)   # 保质期
        self.batch_table.setColumnWidth(6, 120)  # 供应商
        self.batch_table.setColumnWidth(7, 100)  # 批号
        self.batch_table.setColumnWidth(8, 100)  # 查验结果
        self.batch_table.setColumnWidth(9, 110)  # 查验人
        self.batch_table.setColumnWidth(10, 120) # 备注
        self.batch_table.horizontalHeader().setMinimumSectionSize(50)
        self.batch_table.setAlternatingRowColors(True)
        self.batch_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        batch_layout.addWidget(self.batch_table)
        layout.addWidget(batch_group)
        
        # 中间筛选查询区
        filter_group = QGroupBox("筛选查询")
        filter_layout = QHBoxLayout(filter_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索食材名称、供应商、查验人...")
        self.search_edit.returnPressed.connect(self.search_records)
        self.btn_search = QPushButton("🔍 搜索")
        self.btn_search.clicked.connect(self.search_records)
        
        # 默认本月日期范围
        first_day, last_day = self._get_this_month_range()
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(first_day)
        self.date_from.setMinimumWidth(120)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(last_day)
        self.date_to.setMinimumWidth(120)
        
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.load_data)
        
        filter_layout.addWidget(QLabel("日期范围:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("至"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(self.search_edit, 1)
        filter_layout.addWidget(self.btn_search)
        filter_layout.addWidget(self.btn_refresh)
        layout.addWidget(filter_group)
        
        # 底部查验记录列表
        record_group = QGroupBox("查验记录列表")
        record_layout = QVBoxLayout(record_group)
        
        btn_record_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ 添加记录")
        self.btn_add.setObjectName("success")
        self.btn_delete = QPushButton("🗑️ 删除")
        self.btn_delete.setObjectName("danger")
        self.btn_batch_delete = QPushButton("🗑️ 批量删除")
        self.btn_batch_delete.setObjectName("danger")
        
        btn_record_layout.addWidget(self.btn_add)
        btn_record_layout.addWidget(self.btn_delete)
        btn_record_layout.addWidget(self.btn_batch_delete)
        btn_record_layout.addStretch()
        record_layout.addLayout(btn_record_layout)
        
        self.record_table = QTableWidget()
        self.record_table.setColumnCount(9)
        self.record_table.setHorizontalHeaderLabels([
            "✅", "ID", "食材", "数量", "供应商", "批号", 
            "查验结果", "查验人", "查验日期"
        ])
        self.record_table.setColumnWidth(0, 40)
        self.record_table.setColumnHidden(1, True)
        self.record_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.record_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.record_table.setAlternatingRowColors(True)
        self.record_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        record_layout.addWidget(self.record_table)
        layout.addWidget(record_group, 1)
        
        self.btn_add.clicked.connect(self.add_record)
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_batch_delete.clicked.connect(self.batch_delete_records)
        
    def load_data(self):
        """加载查验记录，默认本月数据，未查验的优先显示"""
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        records = InspectionRecordDAO.get_by_date_range(date_from, date_to)
        self._populate_table(records)
    
    def _populate_table(self, records):
        self.record_table.setRowCount(len(records))
        for i, r in enumerate(records):
            # 复选框
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Unchecked)
            self.record_table.setItem(i, 0, check_item)
            
            self.record_table.setItem(i, 1, QTableWidgetItem(str(r.id)))
            self.record_table.setItem(i, 2, QTableWidgetItem(r.ingredient_name))
            self.record_table.setItem(i, 3, QTableWidgetItem(str(r.quantity)))
            self.record_table.setItem(i, 4, QTableWidgetItem(r.supplier_name))
            self.record_table.setItem(i, 5, QTableWidgetItem(r.batch_number))
            self.record_table.setItem(i, 6, QTableWidgetItem(r.inspection_result))
            self.record_table.setItem(i, 7, QTableWidgetItem(r.inspector))
            self.record_table.setItem(i, 8, QTableWidgetItem(r.inspection_date))
    
    def search_records(self):
        """搜索查验记录"""
        keyword = self.search_edit.text().lower().strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        # 先按日期范围获取未查验优先的记录
        records = InspectionRecordDAO.get_by_date_range(date_from, date_to)
        
        # 再过滤关键词
        filtered = []
        for r in records:
            if keyword:
                if keyword not in str(r.ingredient_name).lower() and \
                   keyword not in str(r.supplier_name).lower() and \
                   keyword not in str(r.inspector).lower():
                    continue
            filtered.append(r)
        
        self._populate_table(filtered)
    
    def load_stockin_data(self):
        """加载指定日期的入库数据，并标识已查验的记录"""
        date_str = self.load_date.date().toString("yyyy-MM-dd")
        with get_connection() as conn:
            cursor = conn.cursor()
            # 查询入库数据，并检查是否已有查验记录
            cursor.execute('''
                SELECT si.id, si.ingredient_id, i.name as ingredient_name, 
                       si.quantity, i.unit, si.production_date, si.expiry_date,
                       si.batch_number, s.name as supplier_name,
                       ir.inspector as existing_inspector,
                       ir.inspection_result as existing_result
                FROM stock_in si
                JOIN ingredients i ON si.ingredient_id = i.id
                LEFT JOIN suppliers s ON si.supplier_id = s.id
                LEFT JOIN inspection_records ir ON ir.stock_in_id = si.id
                WHERE strftime('%Y-%m-%d', si.created_at) = ?
                ORDER BY si.created_at DESC
            ''', (date_str,))
            rows = cursor.fetchall()
        
        existing_count = self.batch_table.rowCount()
        start_row = existing_count
        self.batch_table.setRowCount(existing_count + len(rows))
        
        inspected_count = 0
        for i, row in enumerate(rows):
            row_idx = start_row + i
            
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            # 已查验的默认不选中
            if row['existing_inspector']:
                check_item.setCheckState(Qt.CheckState.Unchecked)
                inspected_count += 1
            else:
                check_item.setCheckState(Qt.CheckState.Checked)
            self.batch_table.setItem(row_idx, 0, check_item)
            
            # 显示食材名称，已查验的用绿色标记
            name_item = QTableWidgetItem(row['ingredient_name'])
            if row['existing_inspector']:
                name_item.setForeground(QColor("#34c759"))
            self.batch_table.setItem(row_idx, 1, name_item)
            
            self.batch_table.setItem(row_idx, 2, QTableWidgetItem(str(row['quantity'])))
            self.batch_table.setItem(row_idx, 3, QTableWidgetItem(row['unit'] or ""))
            self.batch_table.setItem(row_idx, 4, QTableWidgetItem(row['production_date'] or ""))
            self.batch_table.setItem(row_idx, 5, QTableWidgetItem(row['expiry_date'] or ""))
            self.batch_table.setItem(row_idx, 6, QTableWidgetItem(row['supplier_name'] or ""))
            self.batch_table.setItem(row_idx, 7, QTableWidgetItem(row['batch_number'] or ""))
            
            # 查验结果下拉框
            result_combo = QComboBox()
            result_combo.addItems(["合格", "不合格"])
            result_combo.setCurrentText(row['existing_result'] or "合格")
            result_combo.setStyleSheet("""
                QComboBox {
                    border: 1px solid #d2d2d7;
                    border-radius: 4px;
                    padding: 1px 4px;
                    background-color: white;
                    min-height: 26px;
                    max-height: 26px;
                    font-size: 12px;
                }
                QComboBox::drop-down {
                    border: none;
                    border-left: 1px solid #d2d2d7;
                    width: 18px;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                    background-color: #f5f5f7;
                }
                QComboBox::down-arrow {
                    width: 5px;
                    height: 5px;
                    border-width: 0 0 2px 2px;
                    border-style: solid;
                    border-color: #86868b;
                    transform: rotate(-45deg);
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #d2d2d7;
                    border-radius: 6px;
                    background-color: white;
                    selection-background-color: #0071e3;
                }
            """)
            self.batch_table.setCellWidget(row_idx, 8, result_combo)
            
            # 查验人下拉框
            inspector_combo = QComboBox()
            inspector_combo.setEditable(True)
            inspectors = InspectorDAO.get_active()
            if inspectors:
                inspector_combo.addItems([i.name for i in inspectors])
            if row['existing_inspector']:
                inspector_combo.setCurrentText(row['existing_inspector'])
            inspector_combo.setStyleSheet("""
                QComboBox {
                    border: 1px solid #d2d2d7;
                    border-radius: 4px;
                    padding: 1px 4px;
                    background-color: white;
                    min-height: 26px;
                    max-height: 26px;
                    font-size: 12px;
                }
                QComboBox::drop-down {
                    border: none;
                    border-left: 1px solid #d2d2d7;
                    width: 18px;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                    background-color: #f5f5f7;
                }
                QComboBox::down-arrow {
                    width: 5px;
                    height: 5px;
                    border-width: 0 0 2px 2px;
                    border-style: solid;
                    border-color: #86868b;
                    transform: rotate(-45deg);
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #d2d2d7;
                    border-radius: 6px;
                    background-color: white;
                    selection-background-color: #0071e3;
                }
            """)
            self.batch_table.setCellWidget(row_idx, 9, inspector_combo)
            
            self.batch_table.setItem(row_idx, 10, QTableWidgetItem(""))
            
            # 隐藏列：ingredient_id
            item = QTableWidgetItem(str(row['ingredient_id']))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.batch_table.setItem(row_idx, 11, item)
            
            # 隐藏列：stock_in_id
            stock_in_id_item = QTableWidgetItem(str(row['id']))
            stock_in_id_item.setFlags(stock_in_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.batch_table.setItem(row_idx, 12, stock_in_id_item)
        
        if rows:
            msg = f"已加载 {len(rows)} 条入库数据"
            if inspected_count > 0:
                msg += f"（其中 {inspected_count} 条已查验，显示为绿色）"
            self.show_info(msg)
        else:
            self.show_info(f"{date_str} 没有入库数据")
    
    def batch_set_fields(self):
        """批量设置查验结果和查验人"""
        result = self.batch_result_combo.currentText()
        inspector = self.batch_inspector_combo.currentText().strip()
        
        if not inspector:
            self.show_warning("请选择或输入查验人姓名")
            return
        
        count = 0
        for i in range(self.batch_table.rowCount()):
            check_item = self.batch_table.item(i, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                # 设置查验结果下拉框
                result_combo = self.batch_table.cellWidget(i, 8)
                if result_combo:
                    result_combo.setCurrentText(result)
                
                # 设置查验人下拉框
                inspector_combo = self.batch_table.cellWidget(i, 9)
                if inspector_combo:
                    inspector_combo.setCurrentText(inspector)
                
                count += 1
        
        self.show_info(f"已批量设置 {count} 条记录")
    
    def select_all_batch(self):
        """全选批量表格"""
        for i in range(self.batch_table.rowCount()):
            check_item = self.batch_table.item(i, 0)
            if check_item:
                check_item.setCheckState(Qt.CheckState.Checked)
    
    def unselect_all_batch(self):
        """取消全选批量表格"""
        for i in range(self.batch_table.rowCount()):
            check_item = self.batch_table.item(i, 0)
            if check_item:
                check_item.setCheckState(Qt.CheckState.Unchecked)
    
    def delete_selected_batch_rows(self):
        """删除选中的批量行"""
        rows_to_delete = []
        for i in range(self.batch_table.rowCount()):
            check_item = self.batch_table.item(i, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                rows_to_delete.append(i)
        
        if not rows_to_delete:
            self.show_warning("请先选择要删除的行")
            return
        
        for i in reversed(rows_to_delete):
            self.batch_table.removeRow(i)
    
    def clear_batch_table(self):
        """清空批量表格"""
        if self.batch_table.rowCount() > 0:
            if self.confirm("确定要清空批量录入表格吗？"):
                self.batch_table.setRowCount(0)
    
    def batch_save(self):
        records = []
        for i in range(self.batch_table.rowCount()):
            check_item = self.batch_table.item(i, 0)
            if not check_item or check_item.checkState() != Qt.CheckState.Checked:
                continue
            
            ingredient_name_item = self.batch_table.item(i, 1)
            quantity_item = self.batch_table.item(i, 2)
            unit_item = self.batch_table.item(i, 3)
            
            if not ingredient_name_item or not quantity_item or not unit_item:
                continue
            
            ingredient_id_item = self.batch_table.item(i, 11)
            if ingredient_id_item:
                ingredient_id = int(ingredient_id_item.text())
            else:
                ingredients = IngredientDAO.get_all()
                ing = next((x for x in ingredients if x.name == ingredient_name_item.text()), None)
                if not ing:
                    continue
                ingredient_id = ing.id
            
            # 获取 stock_in_id（如果有）
            stock_in_id = None
            stock_in_id_item = self.batch_table.item(i, 12)
            if stock_in_id_item and stock_in_id_item.text():
                try:
                    stock_in_id = int(stock_in_id_item.text())
                except ValueError:
                    stock_in_id = None
            
            try:
                quantity = float(quantity_item.text())
            except ValueError:
                continue
            
            # 从下拉框获取查验结果和查验人
            result_combo = self.batch_table.cellWidget(i, 8)
            inspection_result = result_combo.currentText() if result_combo else ""
            
            inspector_combo = self.batch_table.cellWidget(i, 9)
            inspector = inspector_combo.currentText().strip() if inspector_combo else ""
            
            if not inspector:
                self.show_warning(f"第 {i+1} 行查验人为空，请填写后再保存")
                return
            
            record = {
                'stock_in_id': stock_in_id,
                'ingredient_id': ingredient_id,
                'quantity': quantity,
                'unit': unit_item.text(),
                'production_date': self.batch_table.item(i, 4).text() if self.batch_table.item(i, 4) else "",
                'shelf_life': self.batch_table.item(i, 5).text() if self.batch_table.item(i, 5) else "",
                'supplier_name': self.batch_table.item(i, 6).text() if self.batch_table.item(i, 6) else "",
                'batch_number': self.batch_table.item(i, 7).text() if self.batch_table.item(i, 7) else "",
                'inspection_result': inspection_result,
                'inspector': inspector,
                'inspection_date': datetime.now().strftime("%Y-%m-%d"),
                'remark': self.batch_table.item(i, 10).text() if self.batch_table.item(i, 10) else ""
            }
            records.append(record)
        
        if records:
            insert_count, update_count = InspectionRecordDAO.batch_add_or_update(records)
            self.show_info(f"保存成功！新增 {insert_count} 条，更新 {update_count} 条")
            LogDAO.add(None, "批量保存查验记录", "inspection_record", 0, f"新增 {insert_count} 条，更新 {update_count} 条")
            self.load_data()
            self.batch_table.setRowCount(0)
        else:
            self.show_error("没有选中的可保存数据")
    
    def add_record(self):
        dialog = InspectionRecordEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            InspectionRecordDAO.add(**data)
            self.show_info("添加成功")
            LogDAO.add(None, "添加查验记录", "inspection_record", 0, f"食材ID: {data['ingredient_id']}")
            self.load_data()
    
    def delete_record(self):
        row = self.record_table.currentRow()
        if row < 0:
            self.show_error("请选择要删除的记录")
            return
        
        record_id = int(self.record_table.item(row, 1).text())
        
        if self.confirm("确定要删除该查验记录吗？"):
            if InspectionRecordDAO.delete(record_id):
                self.show_info("删除成功")
                LogDAO.add(None, "删除查验记录", "inspection_record", record_id, "")
                self.load_data()
            else:
                self.show_error("删除失败，记录可能不存在或已被删除")
    
    def batch_delete_records(self):
        """批量删除选中的查验记录"""
        selected_ids = []
        for i in range(self.record_table.rowCount()):
            check_item = self.record_table.item(i, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                record_id = int(self.record_table.item(i, 1).text())
                selected_ids.append(record_id)
        
        if not selected_ids:
            self.show_error("请先勾选要删除的记录")
            return
        
        if self.show_warning(
            f"确定要删除选中的 {len(selected_ids)} 条查验记录吗？\n\n"
            "⚠️ 警告：此操作不可撤销，将永久删除这些记录！",
            "批量删除确认"
        ):
            deleted_count = 0
            for record_id in selected_ids:
                if InspectionRecordDAO.delete(record_id):
                    deleted_count += 1
                    LogDAO.add(None, "批量删除查验记录", "inspection_record", record_id, "")
            
            self.show_info(f"批量删除完成，共删除 {deleted_count} 条记录")
            self.load_data()


class InspectionRecordEditDialog(BaseDialog):
    """进货查验记录编辑对话框"""
    def __init__(self, parent=None, record_id=None):
        super().__init__(parent, "编辑查验记录" if record_id else "添加查验记录")
        self.record_id = record_id
        self.setMinimumWidth(550)
        self.setup_ui()
        self.load_inspectors()
    
    def load_inspectors(self):
        """加载查验人员列表"""
        inspectors = InspectorDAO.get_active()
        self.inspector_combo.clear()
        if inspectors:
            self.inspector_combo.addItems([i.name for i in inspectors])
        else:
            self.inspector_combo.addItem("请先添加查验人员")
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.ingredient_combo = QComboBox()
        self.load_ingredients()

        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(999999)
        self.quantity_spin.setValue(0)

        self.unit_edit = QLineEdit()

        self.production_date = QDateEdit()
        self.production_date.setDate(QDate.currentDate())

        self.shelf_life_edit = QLineEdit()

        self.supplier_name_edit = QLineEdit()

        self.batch_edit = QLineEdit()

        self.result_combo = QComboBox()
        self.result_combo.addItems(["合格", "不合格", "待复检"])

        self.inspector_combo = QComboBox()
        self.inspector_combo.setEditable(True)

        self.certificate_edit = QLineEdit()

        self.remark_edit = QLineEdit()
        for w in [self.ingredient_combo, self.quantity_spin, self.unit_edit, self.production_date,
                  self.shelf_life_edit, self.supplier_name_edit, self.batch_edit,
                  self.result_combo, self.inspector_combo, self.certificate_edit, self.remark_edit]:
            w.setMinimumWidth(250)

        layout.addRow("食材*:", self.ingredient_combo)
        layout.addRow("数量*:", self.quantity_spin)
        layout.addRow("单位*:", self.unit_edit)
        layout.addRow("生产日期:", self.production_date)
        layout.addRow("保质期:", self.shelf_life_edit)
        layout.addRow("供应商名称:", self.supplier_name_edit)
        layout.addRow("批号:", self.batch_edit)
        layout.addRow("查验结果:", self.result_combo)
        layout.addRow("查验人:", self.inspector_combo)
        layout.addRow("合格证号:", self.certificate_edit)
        layout.addRow("备注:", self.remark_edit)

        self.btn_save = QPushButton("保存")
        self.btn_save.setObjectName("success")
        self.btn_save.setMinimumWidth(80)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setMinimumWidth(80)
        btn_layout = self.create_button_layout(self.btn_save, self.btn_cancel)
        layout.addRow("", btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.ingredient_combo.currentIndexChanged.connect(self.on_ingredient_changed)
    
    def load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = IngredientDAO.get_all()
        for ing in ingredients:
            self.ingredient_combo.addItem(f"{ing.name} ({ing.unit})", ing.id)
    
    def on_ingredient_changed(self):
        ingredient_id = self.ingredient_combo.currentData()
        if ingredient_id:
            ingredient = IngredientDAO.get_by_id(ingredient_id)
            if ingredient:
                self.unit_edit.setText(ingredient.unit)
    
    def get_data(self):
        return {
            'ingredient_id': self.ingredient_combo.currentData(),
            'quantity': self.quantity_spin.value(),
            'unit': self.unit_edit.text(),
            'production_date': self.production_date.date().toString("yyyy-MM-dd"),
            'shelf_life': self.shelf_life_edit.text(),
            'supplier_name': self.supplier_name_edit.text(),
            'batch_number': self.batch_edit.text(),
            'inspection_result': self.result_combo.currentText(),
            'inspector': self.inspector_combo.currentText(),
            'inspection_date': datetime.now().strftime("%Y-%m-%d"),
            'certificate_no': self.certificate_edit.text(),
            'remark': self.remark_edit.text()
        }


class StockOutDialog(BaseDialog):
    """出库管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "出库管理")
        self.setMinimumWidth(1000)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 顶部批量出库操作区
        batch_group = QGroupBox("批量出库")
        batch_layout = QVBoxLayout(batch_group)
        
        btn_batch_layout = QHBoxLayout()
        self.btn_load_stockin = QPushButton("📥 加载今日入库数据")
        self.btn_load_stockin.setObjectName("success")
        self.btn_load_stockin.clicked.connect(self.load_today_stockin)
        
        self.btn_load_all = QPushButton("📋 加载所有库存")
        self.btn_load_all.setObjectName("success")
        self.btn_load_all.clicked.connect(self.load_all_stock)
        
        self.btn_select_all = QPushButton("✅ 全选")
        self.btn_select_all.clicked.connect(self.select_all_rows)
        
        self.btn_deselect_all = QPushButton("❎ 取消全选")
        self.btn_deselect_all.clicked.connect(self.deselect_all_rows)
        
        self.btn_delete_selected = QPushButton("🗑️ 删除选中行")
        self.btn_delete_selected.setObjectName("danger")
        self.btn_delete_selected.clicked.connect(self.delete_selected_rows)
        
        self.btn_batch_out = QPushButton("🚀 批量出库")
        self.btn_batch_out.setObjectName("warning")
        self.btn_batch_out.clicked.connect(self.batch_stock_out)
        
        btn_batch_layout.addWidget(self.btn_load_stockin)
        btn_batch_layout.addWidget(self.btn_load_all)
        btn_batch_layout.addWidget(self.btn_select_all)
        btn_batch_layout.addWidget(self.btn_deselect_all)
        btn_batch_layout.addWidget(self.btn_delete_selected)
        btn_batch_layout.addWidget(self.btn_batch_out)
        btn_batch_layout.addStretch()
        batch_layout.addLayout(btn_batch_layout)
        
        # 批量编辑表格
        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(9)
        self.batch_table.setHorizontalHeaderLabels([
            "选择", "食材", "当前库存", "单位", "出库数量", "用途", "领用部门", "操作人", "ID"
        ])
        self.batch_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.batch_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.batch_table.setColumnHidden(8, True)
        self.batch_table.setAlternatingRowColors(True)
        
        batch_layout.addWidget(self.batch_table)
        layout.addWidget(batch_group)
        
        # 单条出库表单区
        form_group = QGroupBox("单条出库")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 第一行：食材和数量
        row1 = QHBoxLayout()
        self.ingredient_combo = QComboBox()
        self.load_ingredients()
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setPrefix("数量: ")
        
        row1.addWidget(QLabel("食材*:"))
        row1.addWidget(self.ingredient_combo, 1)
        row1.addWidget(self.quantity_spin)
        form_layout.addRow(row1)
        
        # 第二行：单价、用途、领用部门
        row2 = QHBoxLayout()
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        self.price_spin.setPrefix("¥ ")
        self.purpose_edit = QLineEdit()
        self.purpose_edit.setPlaceholderText("用途")
        self.department_edit = QLineEdit()
        self.department_edit.setPlaceholderText("领用部门")
        
        row2.addWidget(QLabel("单价:"))
        row2.addWidget(self.price_spin)
        row2.addWidget(QLabel("用途:"))
        row2.addWidget(self.purpose_edit, 1)
        row2.addWidget(QLabel("领用部门:"))
        row2.addWidget(self.department_edit, 1)
        form_layout.addRow(row2)
        
        # 第三行：操作人、备注、按钮
        row3 = QHBoxLayout()
        self.operator_edit = QLineEdit()
        self.operator_edit.setPlaceholderText("操作人")
        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("备注")
        self.btn_out = QPushButton("📤 确认出库")
        self.btn_out.setObjectName("warning")
        self.btn_out.setMinimumWidth(120)
        
        row3.addWidget(QLabel("操作人:"))
        row3.addWidget(self.operator_edit, 1)
        row3.addWidget(QLabel("备注:"))
        row3.addWidget(self.remark_edit, 1)
        row3.addWidget(self.btn_out)
        form_layout.addRow(row3)
        
        layout.addWidget(form_group)
        
        # 筛选查询区
        filter_group = QGroupBox("筛选查询")
        filter_layout = QHBoxLayout(filter_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索食材名称、用途、操作人...")
        self.search_edit.returnPressed.connect(self.search_records)
        self.btn_search = QPushButton("🔍 搜索")
        self.btn_search.clicked.connect(self.search_records)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.load_data)
        
        filter_layout.addWidget(QLabel("日期范围:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("至"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(self.search_edit, 1)
        filter_layout.addWidget(self.btn_search)
        filter_layout.addWidget(self.btn_refresh)
        layout.addWidget(filter_group)
        
        # 底部出库记录表格
        record_group = QGroupBox("出库记录")
        record_layout = QVBoxLayout(record_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材", "数量", "用途", "领用部门", "操作人", "备注", "出库时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        record_layout.addWidget(self.table)
        layout.addWidget(record_group, 1)
        
        self.btn_out.clicked.connect(self.do_stock_out)
        self.ingredient_combo.currentIndexChanged.connect(self.on_ingredient_changed)
        
    def load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = IngredientDAO.get_all()
        for ing in ingredients:
            self.ingredient_combo.addItem(
                f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id
            )
    
    def on_ingredient_changed(self):
        ingredient_id = self.ingredient_combo.currentData()
        if ingredient_id:
            ingredient = IngredientDAO.get_by_id(ingredient_id)
            if ingredient:
                self.quantity_spin.setMaximum(ingredient.current_stock)
    
    def load_data(self):
        records = StockOutDAO.get_all()
        self._populate_table(records)
    
    def _populate_table(self, records):
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.id)))
            self.table.setItem(i, 1, QTableWidgetItem(r.ingredient_name))
            self.table.setItem(i, 2, QTableWidgetItem(str(r.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(r.purpose))
            self.table.setItem(i, 4, QTableWidgetItem(r.department))
            self.table.setItem(i, 5, QTableWidgetItem(r.operator))
            self.table.setItem(i, 6, QTableWidgetItem(r.remark))
            self.table.setItem(i, 7, QTableWidgetItem(r.created_at[:19]))
    
    def search_records(self):
        keyword = self.search_edit.text().lower().strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        records = StockOutDAO.get_all()
        filtered = []
        for r in records:
            record_date = r.created_at[:10]
            if record_date < date_from or record_date > date_to:
                continue
            if keyword:
                if keyword not in str(r.ingredient_name).lower() and \
                   keyword not in str(r.purpose).lower() and \
                   keyword not in str(r.operator).lower():
                    continue
            filtered.append(r)
        
        self._populate_table(filtered)
    
    def load_today_stockin(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT si.ingredient_id, i.name as ingredient_name, 
                       i.current_stock, i.unit, si.quantity as stockin_quantity
                FROM stock_in si
                JOIN ingredients i ON si.ingredient_id = i.id
                WHERE strftime('%Y-%m-%d', si.created_at) = ?
                GROUP BY si.ingredient_id
            ''', (today,))
            rows = cursor.fetchall()
        
        self.batch_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            # 复选框列
            chk_item = QTableWidgetItem()
            chk_item.setCheckState(Qt.CheckState.Checked)
            self.batch_table.setItem(i, 0, chk_item)
            # 数据列
            self.batch_table.setItem(i, 1, QTableWidgetItem(row['ingredient_name']))
            self.batch_table.setItem(i, 2, QTableWidgetItem(str(row['current_stock'])))
            self.batch_table.setItem(i, 3, QTableWidgetItem(row['unit']))
            self.batch_table.setItem(i, 4, QTableWidgetItem(str(row['stockin_quantity'])))
            self.batch_table.setItem(i, 5, QTableWidgetItem("营养餐"))
            self.batch_table.setItem(i, 6, QTableWidgetItem("食堂"))
            self.batch_table.setItem(i, 7, QTableWidgetItem(""))
            # 隐藏列存储ingredient_id
            item = QTableWidgetItem(str(row['ingredient_id']))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.batch_table.setItem(i, 8, item)
    
    def select_all_rows(self):
        for i in range(self.batch_table.rowCount()):
            item = self.batch_table.item(i, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_rows(self):
        for i in range(self.batch_table.rowCount()):
            item = self.batch_table.item(i, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def delete_selected_rows(self):
        rows_to_remove = []
        for i in range(self.batch_table.rowCount()):
            item = self.batch_table.item(i, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                rows_to_remove.append(i)
        
        for row in sorted(rows_to_remove, reverse=True):
            self.batch_table.removeRow(row)
    
    def load_all_stock(self):
        ingredients = IngredientDAO.get_all()
        self.batch_table.setRowCount(len(ingredients))
        for i, ing in enumerate(ingredients):
            # 复选框列
            chk_item = QTableWidgetItem()
            chk_item.setCheckState(Qt.CheckState.Checked)
            self.batch_table.setItem(i, 0, chk_item)
            # 数据列
            self.batch_table.setItem(i, 1, QTableWidgetItem(ing.name))
            self.batch_table.setItem(i, 2, QTableWidgetItem(str(ing.current_stock)))
            self.batch_table.setItem(i, 3, QTableWidgetItem(ing.unit))
            self.batch_table.setItem(i, 4, QTableWidgetItem(str(ing.current_stock)))
            self.batch_table.setItem(i, 5, QTableWidgetItem("营养餐"))
            self.batch_table.setItem(i, 6, QTableWidgetItem("食堂"))
            self.batch_table.setItem(i, 7, QTableWidgetItem(""))
            # 隐藏列存储ingredient_id
            item = QTableWidgetItem(str(ing.id))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.batch_table.setItem(i, 8, item)
    
    def batch_stock_out(self):
        success_count = 0
        error_count = 0
        errors = []
        success_items = []  # 记录成功的行索引，用于成功后清除

        for i in range(self.batch_table.rowCount()):
            # 检查复选框是否选中
            chk_item = self.batch_table.item(i, 0)
            if not chk_item or chk_item.checkState() != Qt.CheckState.Checked:
                continue

            ingredient_id_item = self.batch_table.item(i, 8)
            quantity_item = self.batch_table.item(i, 4)

            if not ingredient_id_item or not quantity_item:
                continue

            ingredient_id = int(ingredient_id_item.text())

            try:
                quantity = float(quantity_item.text())
            except ValueError:
                error_count += 1
                errors.append(f"第{i+1}行: 数量格式错误")
                continue

            if quantity <= 0:
                error_count += 1
                errors.append(f"第{i+1}行: 数量必须大于0")
                continue

            purpose = self.batch_table.item(i, 5).text() if self.batch_table.item(i, 5) else "营养餐"
            department = self.batch_table.item(i, 6).text() if self.batch_table.item(i, 6) else "食堂"
            operator = self.batch_table.item(i, 7).text() if self.batch_table.item(i, 7) else ""

            try:
                success, msg = StockOutDAO.add(
                    ingredient_id=ingredient_id,
                    quantity=quantity,
                    unit_price=0,
                    purpose=purpose,
                    department=department,
                    operator=operator,
                    remark="批量出库"
                )

                if success:
                    success_count += 1
                    success_items.append(i)
                else:
                    error_count += 1
                    errors.append(f"{self.batch_table.item(i, 1).text()}: {msg}")
            except Exception as e:
                error_count += 1
                errors.append(f"{self.batch_table.item(i, 1).text()}: {str(e)}")

        result_msg = f"批量出库完成!\n成功: {success_count} 条\n失败: {error_count} 条"
        if errors:
            result_msg += "\n\n错误详情:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                result_msg += f"\n... 还有 {len(errors) - 5} 条错误"

        if success_count > 0:
            self.show_info(result_msg)
            LogDAO.add(None, "批量出库", "stock_out", 0, f"成功 {success_count} 条")
            self.load_data()
            self.load_ingredients()
            self.batch_table.setRowCount(0)
        else:
            self.show_error(result_msg)
    
    def do_stock_out(self):
        ingredient_id = self.ingredient_combo.currentData()
        quantity = self.quantity_spin.value()

        if not ingredient_id or quantity <= 0:
            self.show_error("请填写完整的出库信息")
            return

        try:
            success, msg = StockOutDAO.add(
                ingredient_id=ingredient_id,
                quantity=quantity,
                unit_price=self.price_spin.value(),
                purpose=self.purpose_edit.text(),
                department=self.department_edit.text(),
                operator=self.operator_edit.text(),
                remark=self.remark_edit.text()
            )

            if success:
                self.show_info(msg)
                LogDAO.add(None, "出库", "stock_out", 0, f"食材ID: {ingredient_id}, 数量: {quantity}")
                self.load_data()
                self.load_ingredients()

                self.quantity_spin.setValue(1)
                self.price_spin.setValue(0)
                self.purpose_edit.clear()
                self.remark_edit.clear()
            else:
                self.show_error(msg)
        except Exception as e:
            self.show_error(f"出库操作异常: {str(e)}")


class InventoryCheckDialog(BaseDialog):
    """库存盘点对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "库存盘点")
        self.setMinimumWidth(1000)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 顶部操作区 - 新增盘点表单
        form_group = QGroupBox("新增盘点")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 第一行：食材、系统库存、实际库存
        row1 = QHBoxLayout()
        self.ingredient_combo = QComboBox()
        self.load_ingredients()
        self.system_stock_label = QLabel("-")
        self.system_stock_label.setStyleSheet("font-weight: 600; color: #0071e3;")
        self.actual_stock_spin = QDoubleSpinBox()
        self.actual_stock_spin.setMaximum(999999)
        self.actual_stock_spin.setValue(0)
        self.actual_stock_spin.setPrefix("实际: ")
        
        row1.addWidget(QLabel("食材*:"))
        row1.addWidget(self.ingredient_combo, 1)
        row1.addWidget(QLabel("系统库存:"))
        row1.addWidget(self.system_stock_label)
        row1.addWidget(self.actual_stock_spin)
        form_layout.addRow(row1)
        
        # 第二行：盘点人、备注、按钮
        row2 = QHBoxLayout()
        self.operator_edit = QLineEdit()
        self.operator_edit.setPlaceholderText("盘点人")
        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("备注")
        self.btn_check = QPushButton("✅ 确认盘点")
        self.btn_check.setObjectName("success")
        self.btn_check.setMinimumWidth(120)
        
        row2.addWidget(QLabel("盘点人:"))
        row2.addWidget(self.operator_edit)
        row2.addWidget(QLabel("备注:"))
        row2.addWidget(self.remark_edit, 1)
        row2.addWidget(self.btn_check)
        form_layout.addRow(row2)
        
        layout.addWidget(form_group)
        
        # 中间筛选区
        filter_group = QGroupBox("筛选查询")
        filter_layout = QHBoxLayout(filter_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索食材名称、盘点人...")
        self.search_edit.returnPressed.connect(self.search_records)
        self.btn_search = QPushButton("搜索")
        self.btn_search.clicked.connect(self.search_records)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.load_data)
        
        self.btn_batch_check = QPushButton("📋 批量盘点")
        self.btn_batch_check.setObjectName("warning")
        self.btn_batch_check.clicked.connect(self.batch_check)
        
        filter_layout.addWidget(QLabel("日期范围:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("至"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(self.search_edit, 1)
        filter_layout.addWidget(self.btn_search)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addWidget(self.btn_batch_check)
        layout.addWidget(filter_group)
        
        # 底部数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材", "系统库存", "实际库存", "差异", "盘点人", "时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)
        
        self.ingredient_combo.currentIndexChanged.connect(self.on_ingredient_changed)
        self.btn_check.clicked.connect(self.do_check)
        
    def load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = IngredientDAO.get_all()
        for ing in ingredients:
            self.ingredient_combo.addItem(
                f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id
            )
    
    def on_ingredient_changed(self):
        ingredient_id = self.ingredient_combo.currentData()
        if ingredient_id:
            ingredient = IngredientDAO.get_by_id(ingredient_id)
            if ingredient:
                self.system_stock_label.setText(f"{ingredient.current_stock} {ingredient.unit}")
                self.actual_stock_spin.setValue(ingredient.current_stock)
    
    def load_data(self):
        records = InventoryCheckDAO.get_all()
        self._populate_table(records)
    
    def _populate_table(self, records):
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.id)))
            self.table.setItem(i, 1, QTableWidgetItem(r.ingredient_name))
            self.table.setItem(i, 2, QTableWidgetItem(str(r.system_stock)))
            self.table.setItem(i, 3, QTableWidgetItem(str(r.actual_stock)))
            self.table.setItem(i, 4, QTableWidgetItem(str(r.difference)))
            self.table.setItem(i, 5, QTableWidgetItem(r.operator))
            self.table.setItem(i, 6, QTableWidgetItem(r.created_at[:19]))
            
            if r.difference != 0:
                for col in range(7):
                    self.table.item(i, col).setBackground(QColor("#fff5f5"))
    
    def search_records(self):
        keyword = self.search_edit.text().lower().strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        records = InventoryCheckDAO.get_all()
        filtered = []
        for r in records:
            # 日期筛选
            record_date = r.created_at[:10]
            if record_date < date_from or record_date > date_to:
                continue
            # 关键词筛选
            if keyword:
                if keyword not in str(r.ingredient_name).lower() and \
                   keyword not in str(r.operator).lower():
                    continue
            filtered.append(r)
        
        self._populate_table(filtered)
    
    def batch_check(self):
        ingredients = IngredientDAO.get_all()
        if not ingredients:
            self.show_error("暂无食材数据")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("批量盘点")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_auto = QPushButton("📋 自动填充系统库存")
        btn_auto.clicked.connect(lambda: self._auto_fill_batch(batch_table))
        btn_confirm = QPushButton("✅ 确认盘点")
        btn_confirm.setObjectName("success")
        btn_cancel = QPushButton("取消")
        
        btn_layout.addWidget(btn_auto)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        # 批量表格
        batch_table = QTableWidget()
        batch_table.setColumnCount(6)
        batch_table.setHorizontalHeaderLabels(["食材", "单位", "系统库存", "实际库存", "差异", "ID"])
        batch_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        batch_table.setRowCount(len(ingredients))
        batch_table.setAlternatingRowColors(True)
        batch_table.setColumnHidden(5, True)
        
        for i, ing in enumerate(ingredients):
            batch_table.setItem(i, 0, QTableWidgetItem(ing.name))
            batch_table.setItem(i, 1, QTableWidgetItem(ing.unit))
            batch_table.setItem(i, 2, QTableWidgetItem(str(ing.current_stock)))
            batch_table.setItem(i, 3, QTableWidgetItem(str(ing.current_stock)))
            batch_table.setItem(i, 4, QTableWidgetItem("0"))
            
            item_id = QTableWidgetItem(str(ing.id))
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            batch_table.setItem(i, 5, item_id)
        
        batch_table.itemChanged.connect(lambda item: self._update_diff(batch_table, item))
        
        layout.addWidget(batch_table)
        
        btn_confirm.clicked.connect(lambda: self._confirm_batch(dialog, batch_table))
        btn_cancel.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def _auto_fill_batch(self, table):
        for i in range(table.rowCount()):
            sys_stock = table.item(i, 2).text() if table.item(i, 2) else "0"
            table.setItem(i, 3, QTableWidgetItem(sys_stock))
            table.setItem(i, 4, QTableWidgetItem("0"))
    
    def _update_diff(self, table, item):
        if item.column() == 3:
            row = item.row()
            try:
                sys_stock = float(table.item(row, 2).text())
                actual = float(item.text())
                diff = actual - sys_stock
                table.setItem(row, 4, QTableWidgetItem(str(diff)))
            except:
                pass
    
    def _confirm_batch(self, dialog, table):
        operator = self.operator_edit.text() or "系统"
        success_count = 0
        
        for i in range(table.rowCount()):
            try:
                ingredient_id = int(table.item(i, 5).text())
                actual_stock = float(table.item(i, 3).text())
                InventoryCheckDAO.add(
                    ingredient_id=ingredient_id,
                    system_stock=float(table.item(i, 2).text()),
                    actual_stock=actual_stock,
                    operator=operator,
                    remark="批量盘点"
                )
                success_count += 1
            except:
                continue
        
        if success_count > 0:
            self.show_info(f"批量盘点完成!\n成功: {success_count} 条")
            LogDAO.add(None, "批量盘点", "inventory_check", 0, f"成功 {success_count} 条")
            self.load_data()
            self.load_ingredients()
            dialog.accept()
        else:
            self.show_error("盘点失败，请检查数据")
    
    def do_check(self):
        ingredient_id = self.ingredient_combo.currentData()
        actual_stock = self.actual_stock_spin.value()
        
        if not ingredient_id:
            self.show_error("请选择食材")
            return
        
        ingredient = IngredientDAO.get_by_id(ingredient_id)
        if not ingredient:
            self.show_error("食材不存在")
            return
        
        system_stock = ingredient.current_stock
        
        try:
            InventoryCheckDAO.add(
                ingredient_id=ingredient_id,
                system_stock=system_stock,
                actual_stock=actual_stock,
                operator=self.operator_edit.text(),
                remark=self.remark_edit.text()
            )
        except ValueError as e:
            self.show_error(str(e))
            return
        
        diff = actual_stock - system_stock
        self.show_info(f"盘点完成!\n系统库存: {system_stock}\n实际库存: {actual_stock}\n差异: {diff}")
        LogDAO.add(None, "库存盘点", "inventory_check", 0, 
                   f"食材: {ingredient.name}, 差异: {diff}")
        self.load_data()
        self.load_ingredients()


class ReportWidget(QWidget):
    """报表统计页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.card_total = self.create_stat_card("食材种类", "0", "#0071e3")
        self.card_stock = self.create_stat_card("总库存量", "0", "#34c759")
        self.card_low = self.create_stat_card("库存预警", "0", "#ff3b30")
        self.card_value = self.create_stat_card("库存总值", "¥0.00", "#ff9500")
        
        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_stock)
        cards_layout.addWidget(self.card_low)
        cards_layout.addWidget(self.card_value)
        
        layout.addLayout(cards_layout)
        
        group1 = QGroupBox("分类库存统计")
        group1_layout = QVBoxLayout(group1)
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(4)
        self.category_table.setHorizontalHeaderLabels(["分类", "食材种数", "总库存", "安全库存"])
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        group1_layout.addWidget(self.category_table)
        layout.addWidget(group1)
        
        group2 = QGroupBox("库存预警（低于安全库存）")
        group2_layout = QVBoxLayout(group2)
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(5)
        self.low_stock_table.setHorizontalHeaderLabels(["食材", "分类", "当前库存", "安全库存", "缺口"])
        self.low_stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        group2_layout.addWidget(self.low_stock_table)
        layout.addWidget(group2)
        
        self.btn_refresh = QPushButton("刷新数据")
        self.btn_refresh.setObjectName("success")
        self.btn_refresh.clicked.connect(self.load_data)
        layout.addWidget(self.btn_refresh)
        
    def create_stat_card(self, label, value, accent_color="#0071e3"):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 16px;
                padding: 20px;
            }}
            QLabel#stat_number {{
                color: {accent_color};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        value_label = QLabel(value)
        value_label.setObjectName("stat_number")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        text_label = QLabel(label)
        text_label.setObjectName("stat_label")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(value_label)
        layout.addWidget(text_label)
        
        return card
    
    def update_card_value(self, card, value):
        layout = card.layout()
        value_label = layout.itemAt(0).widget()
        value_label.setText(value)
    
    def load_data(self):
        ingredients = IngredientDAO.get_all()
        total_types = len(ingredients)
        total_stock = sum(ing.current_stock for ing in ingredients)
        low_stock = IngredientDAO.get_low_stock()
        low_count = len(low_stock)
        total_value = ReportDAO.get_inventory_value()
        
        self.update_card_value(self.card_total, str(total_types))
        self.update_card_value(self.card_stock, f"{total_stock:.2f}")
        self.update_card_value(self.card_low, str(low_count))
        self.update_card_value(self.card_value, f"¥{total_value:.2f}")
        
        summary = ReportDAO.get_stock_summary()
        self.category_table.setRowCount(len(summary))
        for i, row in enumerate(summary):
            self.category_table.setItem(i, 0, QTableWidgetItem(row['category_name']))
            self.category_table.setItem(i, 1, QTableWidgetItem(str(row['ingredient_count'])))
            self.category_table.setItem(i, 2, QTableWidgetItem(f"{row['total_stock']:.2f}"))
            self.category_table.setItem(i, 3, QTableWidgetItem(f"{row['total_safety_stock']:.2f}"))
        
        self.low_stock_table.setRowCount(len(low_stock))
        for i, ing in enumerate(low_stock):
            self.low_stock_table.setItem(i, 0, QTableWidgetItem(ing.name))
            self.low_stock_table.setItem(i, 1, QTableWidgetItem(ing.category_name))
            self.low_stock_table.setItem(i, 2, QTableWidgetItem(str(ing.current_stock)))
            self.low_stock_table.setItem(i, 3, QTableWidgetItem(str(ing.safety_stock)))
            diff = ing.safety_stock - ing.current_stock
            self.low_stock_table.setItem(i, 4, QTableWidgetItem(f"{diff:.2f}"))


class FinanceWidget(QWidget):
    """财务统计页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("年份:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(datetime.now().year)
        filter_layout.addWidget(self.year_spin)

        filter_layout.addWidget(QLabel("月份:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(datetime.now().month)
        filter_layout.addWidget(self.month_spin)

        self.btn_query = QPushButton("查询")
        self.btn_query.setObjectName("success")
        self.btn_query.clicked.connect(self.load_data)
        filter_layout.addWidget(self.btn_query)

        self.btn_year_view = QPushButton("年度趋势")
        self.btn_year_view.setObjectName("secondary")
        self.btn_year_view.clicked.connect(self.show_year_trend)
        filter_layout.addWidget(self.btn_year_view)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.card_in = self.create_stat_card("本月采购支出", "¥0.00", "#ff3b30")
        self.card_out = self.create_stat_card("本月出库成本", "¥0.00", "#ff9500")
        self.card_diff = self.create_stat_card("本月差额", "¥0.00", "#0071e3")

        cards_layout.addWidget(self.card_in)
        cards_layout.addWidget(self.card_out)
        cards_layout.addWidget(self.card_diff)

        layout.addLayout(cards_layout)

        group1 = QGroupBox("分类采购金额")
        group1_layout = QVBoxLayout(group1)
        self.category_in_table = QTableWidget()
        self.category_in_table.setColumnCount(3)
        self.category_in_table.setHorizontalHeaderLabels(["分类", "采购金额", "占比"])
        self.category_in_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        group1_layout.addWidget(self.category_in_table)
        layout.addWidget(group1)

        group2 = QGroupBox("供应商采购金额")
        group2_layout = QVBoxLayout(group2)
        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(3)
        self.supplier_table.setHorizontalHeaderLabels(["供应商", "采购金额", "占比"])
        self.supplier_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        group2_layout.addWidget(self.supplier_table)
        layout.addWidget(group2)

        self.year_group = QGroupBox("年度月度趋势")
        year_layout = QVBoxLayout(self.year_group)
        self.year_table = QTableWidget()
        self.year_table.setColumnCount(4)
        self.year_table.setHorizontalHeaderLabels(["月份", "采购支出", "出库成本", "差额"])
        self.year_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        year_layout.addWidget(self.year_table)
        layout.addWidget(self.year_group)
        self.year_group.setVisible(False)

    def create_stat_card(self, label, value, accent_color="#0071e3"):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 16px;
                padding: 20px;
            }}
            QLabel#stat_number {{
                color: {accent_color};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        value_label = QLabel(value)
        value_label.setObjectName("stat_number")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(label)
        text_label.setObjectName("stat_label")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(text_label)

        return card

    def update_card_value(self, card, value):
        layout = card.layout()
        value_label = layout.itemAt(0).widget()
        value_label.setText(value)

    def load_data(self):
        year = self.year_spin.value()
        month = self.month_spin.value()

        data = ReportDAO.get_monthly_finance(year, month)

        self.update_card_value(self.card_in, f"¥{data['total_in']:,.2f}")
        self.update_card_value(self.card_out, f"¥{data['total_out']:,.2f}")
        diff = data['total_in'] - data['total_out']
        self.update_card_value(self.card_diff, f"¥{diff:,.2f}")

        self.category_in_table.setRowCount(len(data['category_in']))
        total_in = data['total_in']
        for i, row in enumerate(data['category_in']):
            self.category_in_table.setItem(i, 0, QTableWidgetItem(row['category_name']))
            self.category_in_table.setItem(i, 1, QTableWidgetItem(f"¥{row['amount']:,.2f}"))
            pct = (row['amount'] / total_in * 100) if total_in > 0 else 0
            self.category_in_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))

        self.supplier_table.setRowCount(len(data['supplier_amount']))
        for i, row in enumerate(data['supplier_amount']):
            self.supplier_table.setItem(i, 0, QTableWidgetItem(row['supplier_name']))
            self.supplier_table.setItem(i, 1, QTableWidgetItem(f"¥{row['amount']:,.2f}"))
            pct = (row['amount'] / total_in * 100) if total_in > 0 else 0
            self.supplier_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))

    def show_year_trend(self):
        year = self.year_spin.value()
        data = ReportDAO.get_yearly_finance(year)

        self.year_group.setVisible(True)
        self.year_table.setRowCount(len(data))
        for i, row in enumerate(data):
            self.year_table.setItem(i, 0, QTableWidgetItem(row['month_name']))
            self.year_table.setItem(i, 1, QTableWidgetItem(f"¥{row['in_amount']:,.2f}"))
            self.year_table.setItem(i, 2, QTableWidgetItem(f"¥{row['out_amount']:,.2f}"))
            diff = row['in_amount'] - row['out_amount']
            self.year_table.setItem(i, 3, QTableWidgetItem(f"¥{diff:,.2f}"))


class AlertWidget(QWidget):
    """提醒中心页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.card_low = self.create_alert_card("库存预警", "0", "#ff3b30")
        self.card_expiry = self.create_alert_card("即将过期", "0", "#ff9500")
        self.card_expired = self.create_alert_card("已过期", "0", "#8e8e93")

        cards_layout.addWidget(self.card_low)
        cards_layout.addWidget(self.card_expiry)
        cards_layout.addWidget(self.card_expired)

        layout.addLayout(cards_layout)

        group1 = QGroupBox("库存预警（低于安全库存）")
        group1_layout = QVBoxLayout(group1)
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(6)
        self.low_stock_table.setHorizontalHeaderLabels(["食材", "分类", "当前库存", "安全库存", "缺口", "建议操作"])
        self.low_stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        group1_layout.addWidget(self.low_stock_table)
        layout.addWidget(group1)

        group2 = QGroupBox("即将过期（7天内）")
        group2_layout = QVBoxLayout(group2)
        self.expiry_table = QTableWidget()
        self.expiry_table.setColumnCount(5)
        self.expiry_table.setHorizontalHeaderLabels(["食材", "批次号", "数量", "过期日期", "剩余天数"])
        self.expiry_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        group2_layout.addWidget(self.expiry_table)
        layout.addWidget(group2)

        group3 = QGroupBox("已过期食材")
        group3_layout = QVBoxLayout(group3)
        self.expired_table = QTableWidget()
        self.expired_table.setColumnCount(5)
        self.expired_table.setHorizontalHeaderLabels(["食材", "批次号", "数量", "过期日期", "入库时间"])
        self.expired_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        group3_layout.addWidget(self.expired_table)
        layout.addWidget(group3)

        self.btn_refresh = QPushButton("刷新提醒")
        self.btn_refresh.setObjectName("success")
        self.btn_refresh.clicked.connect(self.load_data)
        layout.addWidget(self.btn_refresh)

    def create_alert_card(self, label, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #d2d2d7;
                border-radius: 16px;
                padding: 20px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 13px; color: #86868b;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(text_label)

        return card

    def update_card_value(self, card, value):
        layout = card.layout()
        value_label = layout.itemAt(0).widget()
        value_label.setText(value)

    def load_data(self):
        low_stock = IngredientDAO.get_low_stock()
        self.update_card_value(self.card_low, str(len(low_stock)))

        self.low_stock_table.setRowCount(len(low_stock))
        for i, ing in enumerate(low_stock):
            self.low_stock_table.setItem(i, 0, QTableWidgetItem(ing.name))
            self.low_stock_table.setItem(i, 1, QTableWidgetItem(ing.category_name))
            self.low_stock_table.setItem(i, 2, QTableWidgetItem(f"{ing.current_stock} {ing.unit}"))
            self.low_stock_table.setItem(i, 3, QTableWidgetItem(f"{ing.safety_stock} {ing.unit}"))
            diff = ing.safety_stock - ing.current_stock
            self.low_stock_table.setItem(i, 4, QTableWidgetItem(f"{diff:.2f} {ing.unit}"))
            self.low_stock_table.setItem(i, 5, QTableWidgetItem("请及时采购补货"))

        expiry = ReportDAO.get_expiry_warnings(7)
        self.update_card_value(self.card_expiry, str(len(expiry)))

        self.expiry_table.setRowCount(len(expiry))
        for i, item in enumerate(expiry):
            self.expiry_table.setItem(i, 0, QTableWidgetItem(item['ingredient_name']))
            self.expiry_table.setItem(i, 1, QTableWidgetItem(item['batch_number'] or "-"))
            self.expiry_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            self.expiry_table.setItem(i, 3, QTableWidgetItem(item['expiry_date']))
            days = int(item['days_left'])
            self.expiry_table.setItem(i, 4, QTableWidgetItem(f"{days} 天"))
            if days <= 3:
                for col in range(5):
                    self.expiry_table.item(i, col).setBackground(QColor("#fff5f5"))

        expired = ReportDAO.get_expired_items()
        self.update_card_value(self.card_expired, str(len(expired)))

        self.expired_table.setRowCount(len(expired))
        for i, item in enumerate(expired):
            self.expired_table.setItem(i, 0, QTableWidgetItem(item['ingredient_name']))
            self.expired_table.setItem(i, 1, QTableWidgetItem(item['batch_number'] or "-"))
            self.expired_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            self.expired_table.setItem(i, 3, QTableWidgetItem(item['expiry_date']))
            self.expired_table.setItem(i, 4, QTableWidgetItem(item['created_at'][:10]))
            for col in range(5):
                self.expired_table.item(i, col).setBackground(QColor("#f5f5f5"))


class SettingsWidget(QWidget):
    """系统设置页面"""
    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setStyleSheet(StyleSheet.MAIN_STYLE)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # 数据备份
        group1 = QGroupBox("数据备份与恢复")
        g1_layout = QVBoxLayout(group1)
        
        backup_layout = QHBoxLayout()
        self.btn_backup = QPushButton("📥 备份数据")
        self.btn_backup.setObjectName("success")
        self.btn_backup.clicked.connect(self.backup_data)
        
        self.btn_restore = QPushButton("📤 恢复数据")
        self.btn_restore.setObjectName("warning")
        self.btn_restore.clicked.connect(self.restore_data)
        
        backup_layout.addWidget(self.btn_backup)
        backup_layout.addWidget(self.btn_restore)
        backup_layout.addStretch()
        g1_layout.addLayout(backup_layout)
        
        layout.addWidget(group1)
        
        # 数据清理 - 危险操作
        group3 = QGroupBox("⚠️ 数据清理（危险操作）")
        group3.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 2px solid #ff3b30;
                border-radius: 12px;
                margin-top: 12px;
                padding: 16px;
                background-color: #fff5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #ff3b30;
                font-size: 14px;
            }
        """)
        g3_layout = QVBoxLayout(group3)
        
        # 范围选择
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("清理范围:"))
        
        self.clear_combo = QComboBox()
        self.clear_combo.addItem("仅清理入库出库记录", "stock_records")
        self.clear_combo.addItem("仅清理查验记录", "inspection_records")
        self.clear_combo.addItem("仅清理盘点记录", "check_records")
        self.clear_combo.addItem("仅清理操作日志", "logs")
        self.clear_combo.addItem("清理所有业务数据（保留食材和供应商）", "all_business")
        self.clear_combo.addItem("⚠️ 全部清空（包含食材供应商用户）", "all_data")
        
        range_layout.addWidget(self.clear_combo, 1)
        g3_layout.addLayout(range_layout)
        
        # 风险提示
        risk_label = QLabel("""
⚠️ <b>风险提示：</b><br>
• 删除的数据<b>无法恢复</b>，请务必先备份！<br>
• 清理入库出库记录将导致库存数据异常，需重新录入<br>
• 清理所有业务数据将丢失所有出入库、查验、盘点记录<br>
• 全部清空将重置系统为初始状态，所有数据永久丢失<br>
• 删除操作会记录到日志，但不影响已删除的数据本身
        """)
        risk_label.setStyleSheet("color: #86868b; font-size: 12px; padding: 10px; background: #fff; border-radius: 6px;")
        risk_label.setWordWrap(True)
        g3_layout.addWidget(risk_label)
        
        # 清理按钮
        clear_btn_layout = QHBoxLayout()
        self.btn_clear_data = QPushButton("🗑️ 清理数据")
        self.btn_clear_data.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ff453a;
            }
        """)
        self.btn_clear_data.clicked.connect(self.clear_data)
        
        clear_btn_layout.addStretch()
        clear_btn_layout.addWidget(self.btn_clear_data)
        g3_layout.addLayout(clear_btn_layout)
        
        layout.addWidget(group3)
        
        # 查验人员管理
        group_inspector = QGroupBox("查验人员管理")
        g_insp_layout = QVBoxLayout(group_inspector)
        
        insp_table_layout = QHBoxLayout()
        self.inspector_table = QTableWidget()
        self.inspector_table.setColumnCount(4)
        self.inspector_table.setHorizontalHeaderLabels(["ID", "姓名", "电话", "部门"])
        self.inspector_table.setColumnHidden(0, True)
        self.inspector_table.setMaximumHeight(150)
        self.inspector_table.setAlternatingRowColors(True)
        insp_table_layout.addWidget(self.inspector_table, 1)
        
        insp_btn_layout = QVBoxLayout()
        self.btn_insp_add = QPushButton("➕ 添加")
        self.btn_insp_add.setObjectName("success")
        self.btn_insp_add.setMaximumWidth(80)
        self.btn_insp_add.clicked.connect(self.add_inspector)
        
        self.btn_insp_edit = QPushButton("✏️ 编辑")
        self.btn_insp_edit.setObjectName("warning")
        self.btn_insp_edit.setMaximumWidth(80)
        self.btn_insp_edit.clicked.connect(self.edit_inspector)
        
        self.btn_insp_delete = QPushButton("🗑️ 删除")
        self.btn_insp_delete.setObjectName("danger")
        self.btn_insp_delete.setMaximumWidth(80)
        self.btn_insp_delete.clicked.connect(self.delete_inspector)
        
        insp_btn_layout.addWidget(self.btn_insp_add)
        insp_btn_layout.addWidget(self.btn_insp_edit)
        insp_btn_layout.addWidget(self.btn_insp_delete)
        insp_btn_layout.addStretch()
        insp_table_layout.addLayout(insp_btn_layout)
        g_insp_layout.addLayout(insp_table_layout)
        
        layout.addWidget(group_inspector)
        
        # 加载查验人员数据
        self.load_inspectors()
        
        # 修改密码
        group2 = QGroupBox("修改密码")
        g2_layout = QFormLayout(group2)
        
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        g2_layout.addRow("原密码:", self.old_pwd)
        g2_layout.addRow("新密码:", self.new_pwd)
        g2_layout.addRow("确认新密码:", self.confirm_pwd)
        
        self.btn_change_pwd = QPushButton("✅ 修改密码")
        self.btn_change_pwd.setObjectName("success")
        self.btn_change_pwd.clicked.connect(self.change_password)
        g2_layout.addRow(self.btn_change_pwd)
        
        layout.addWidget(group2)
        layout.addStretch()
        
    def backup_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "备份数据", f"canteen_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database Files (*.db)"
        )
        if file_path:
            try:
                shutil.copy2(DB_PATH, file_path)
                QMessageBox.information(self, "备份成功", f"数据已备份到:\n{file_path}")
                LogDAO.add(None, "数据备份", "system", 0, f"备份路径: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "备份失败", str(e))
    
    def restore_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "恢复数据", "", "Database Files (*.db)"
        )
        if file_path:
            reply = QMessageBox.question(
                self, "确认恢复", "恢复数据将覆盖当前所有数据，确定继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    shutil.copy2(file_path, DB_PATH)
                    QMessageBox.information(self, "恢复成功", "数据已恢复，请重启程序")
                    LogDAO.add(None, "数据恢复", "system", 0, f"恢复路径: {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "恢复失败", str(e))
    
    def load_inspectors(self):
        """加载查验人员列表"""
        inspectors = InspectorDAO.get_all()
        self.inspector_table.setRowCount(len(inspectors))
        for i, insp in enumerate(inspectors):
            self.inspector_table.setItem(i, 0, QTableWidgetItem(str(insp.id)))
            self.inspector_table.setItem(i, 1, QTableWidgetItem(insp.name))
            self.inspector_table.setItem(i, 2, QTableWidgetItem(insp.phone or ""))
            self.inspector_table.setItem(i, 3, QTableWidgetItem(insp.department or ""))
    
    def add_inspector(self):
        """添加查验人员"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加查验人员")
        dialog.setMinimumWidth(450)
        dialog.setStyleSheet(StyleSheet.MAIN_STYLE)
        layout = QFormLayout(dialog)
        layout.setSpacing(12)

        name_edit = QLineEdit()
        name_edit.setMinimumWidth(250)
        phone_edit = QLineEdit()
        phone_edit.setMinimumWidth(250)
        dept_edit = QLineEdit()
        dept_edit.setMinimumWidth(250)

        layout.addRow("姓名*:", name_edit)
        layout.addRow("电话:", phone_edit)
        layout.addRow("部门:", dept_edit)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)
        btn_box.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.setObjectName("success")
        btn_ok.setMinimumWidth(80)
        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("secondary")
        btn_cancel.setMinimumWidth(80)
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addRow("", btn_box)
        
        def do_add():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dialog, "提示", "姓名不能为空")
                return
            if InspectorDAO.add(name, phone_edit.text().strip(), dept_edit.text().strip()):
                QMessageBox.information(dialog, "成功", "添加成功")
                dialog.accept()
                self.load_inspectors()
            else:
                QMessageBox.warning(dialog, "失败", "添加失败，可能姓名已存在")
        
        btn_ok.clicked.connect(do_add)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec()
    
    def edit_inspector(self):
        """编辑查验人员"""
        row = self.inspector_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择要编辑的人员")
            return
        
        insp_id = int(self.inspector_table.item(row, 0).text())
        old_name = self.inspector_table.item(row, 1).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑查验人员")
        dialog.setMinimumWidth(450)
        dialog.setStyleSheet(StyleSheet.MAIN_STYLE)
        layout = QFormLayout(dialog)
        layout.setSpacing(12)

        name_edit = QLineEdit(old_name)
        name_edit.setMinimumWidth(250)
        phone_edit = QLineEdit(self.inspector_table.item(row, 2).text())
        phone_edit.setMinimumWidth(250)
        dept_edit = QLineEdit(self.inspector_table.item(row, 3).text())
        dept_edit.setMinimumWidth(250)

        layout.addRow("姓名*:", name_edit)
        layout.addRow("电话:", phone_edit)
        layout.addRow("部门:", dept_edit)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)
        btn_box.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.setObjectName("success")
        btn_ok.setMinimumWidth(80)
        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("secondary")
        btn_cancel.setMinimumWidth(80)
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addRow("", btn_box)
        
        def do_update():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dialog, "提示", "姓名不能为空")
                return
            if InspectorDAO.update(insp_id, name=name, phone=phone_edit.text().strip(), department=dept_edit.text().strip()):
                QMessageBox.information(dialog, "成功", "更新成功")
                dialog.accept()
                self.load_inspectors()
            else:
                QMessageBox.warning(dialog, "失败", "更新失败，可能姓名已存在")
        
        btn_ok.clicked.connect(do_update)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec()
    
    def delete_inspector(self):
        """删除查验人员"""
        row = self.inspector_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择要删除的人员")
            return
        
        insp_id = int(self.inspector_table.item(row, 0).text())
        name = self.inspector_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除", f"确定删除查验人员「{name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if InspectorDAO.delete(insp_id):
                QMessageBox.information(self, "成功", "删除成功")
                self.load_inspectors()
            else:
                QMessageBox.warning(self, "失败", "删除失败")
    
    def change_password(self):
        old = self.old_pwd.text()
        new_pwd = self.new_pwd.text()
        confirm = self.confirm_pwd.text()
        
        if not old or not new_pwd:
            QMessageBox.warning(self, "提示", "请填写完整信息")
            return
        
        if new_pwd != confirm:
            QMessageBox.warning(self, "提示", "两次输入的新密码不一致")
            return
        
        if not self.current_user:
            QMessageBox.warning(self, "提示", "未登录用户")
            return
        
        # 验证原密码
        from database import verify_password
        if not verify_password(old, self.current_user.salt, self.current_user.password_hash):
            QMessageBox.warning(self, "提示", "原密码错误")
            return
        
        # 更新密码
        if UserDAO.update_password(self.current_user.id, new_pwd):
            QMessageBox.information(self, "成功", "密码修改成功，请牢记新密码")
            self.old_pwd.clear()
            self.new_pwd.clear()
            self.confirm_pwd.clear()
            LogDAO.add(self.current_user.id, "修改密码", "user", self.current_user.id, "用户修改了自己的密码")
        else:
            QMessageBox.critical(self, "失败", "密码修改失败")
    
    def clear_data(self):
        """清理数据 - 需要二次确认"""
        clear_type = self.clear_combo.currentData()
        clear_name = self.clear_combo.currentText()
        
        # 第一次确认 - 详细风险提示
        warning_msgs = {
            "stock_records": """
<b>即将删除以下数据：</b><br>
• 所有入库记录（stock_in表）<br>
• 所有出库记录（stock_out表）<br><br>
<b>后果：</b><br>
• 所有食材的库存将变为0<br>
• 入库出库历史记录全部丢失<br>
• 无法追溯食材来源和去向<br>
• 相关的财务统计报表将无数据显示
            """,
            "inspection_records": """
<b>即将删除以下数据：</b><br>
• 所有进货查验记录（inspection_records表）<br><br>
<b>后果：</b><br>
• 进货查验历史记录全部丢失<br>
• 无法导出进货查验记录表给监管部门<br>
• 食材验收信息永久丢失
            """,
            "check_records": """
<b>即将删除以下数据：</b><br>
• 所有库存盘点记录（inventory_check表）<br><br>
<b>后果：</b><br>
• 盘点历史记录全部丢失<br>
• 无法追溯库存差异原因<br>
• 盘存盘亏报表将无数据显示
            """,
            "logs": """
<b>即将删除以下数据：</b><br>
• 所有操作日志（logs表）<br><br>
<b>后果：</b><br>
• 操作历史记录全部丢失<br>
• 无法追溯谁在何时做了什么操作<br>
• 系统审计信息丢失
            """,
            "all_business": """
<b>即将删除以下数据：</b><br>
• 所有入库记录（stock_in表）<br>
• 所有出库记录（stock_out表）<br>
• 所有进货查验记录（inspection_records表）<br>
• 所有库存盘点记录（inventory_check表）<br>
• 所有操作日志（logs表）<br><br>
<b>后果：</b><br>
• 所有食材的库存将变为0<br>
• 所有业务历史记录永久丢失<br>
• 系统将只剩基础数据（食材、供应商、分类）<br>
• 所有报表将无数据显示
            """,
            "all_data": """
<b>⚠️ 即将删除以下数据：</b><br>
• 所有入库记录<br>
• 所有出库记录<br>
• 所有进货查验记录<br>
• 所有库存盘点记录<br>
• 所有操作日志<br>
• 所有食材数据<br>
• 所有供应商数据<br>
• 所有分类数据<br>
• 所有类别映射配置<br>
• 所有用户数据（除当前管理员）<br><br>
<b>后果：</b><br>
• 系统将重置为初始状态<br>
• 所有数据永久丢失，无法恢复<br>
• 需要重新录入所有基础数据<br>
• <span style="color:#ff3b30;font-weight:bold;">这是不可逆的操作！</span>
            """
        }
        
        # 第一次确认对话框
        msg1 = QMessageBox(self)
        msg1.setWindowTitle("⚠️ 数据清理确认（第一步）")
        msg1.setIcon(QMessageBox.Icon.Warning)
        msg1.setText(f"<b>清理范围：{clear_name}</b>")
        msg1.setInformativeText(warning_msgs.get(clear_type, ""))
        msg1.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg1.setDefaultButton(QMessageBox.StandardButton.No)
        msg1.button(QMessageBox.StandardButton.Yes).setText("继续确认")
        msg1.button(QMessageBox.StandardButton.No).setText("取消操作")
        
        if msg1.exec() != QMessageBox.StandardButton.Yes:
            return
        
        # 第二次确认 - 需要输入确认文字
        confirm_dialog = QDialog(self)
        confirm_dialog.setWindowTitle("⚠️ 最终确认（第二步）")
        confirm_dialog.setMinimumWidth(400)
        confirm_layout = QVBoxLayout(confirm_dialog)
        
        confirm_label = QLabel("""
<b style="color:#ff3b30;">⚠️ 最后一步确认</b><br><br>
请在下方输入框中输入 "<b>确认删除</b>" 四个字，<br>
然后点击"执行清理"按钮来完成数据清理操作。<br><br>
<span style="color:#86868b;">输入正确的确认文字后，系统将立即执行删除，<br>
此操作<b>不可撤销</b>，请确保已备份数据！</span>
        """)
        confirm_label.setStyleSheet("padding: 20px;")
        confirm_layout.addWidget(confirm_label)
        
        confirm_input = QLineEdit()
        confirm_input.setPlaceholderText("请输入：确认删除")
        confirm_input.setStyleSheet("padding: 10px; font-size: 14px; border: 2px solid #ff3b30;")
        confirm_layout.addWidget(confirm_input)
        
        btn_layout = QHBoxLayout()
        btn_execute = QPushButton("执行清理")
        btn_execute.setStyleSheet("background-color: #ff3b30; color: white; padding: 10px 20px; font-weight: 600;")
        btn_execute.setEnabled(False)
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet("padding: 10px 20px;")
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_execute)
        btn_layout.addWidget(btn_cancel)
        confirm_layout.addLayout(btn_layout)
        
        # 监听输入，只有输入"确认删除"才能点击执行按钮
        confirm_input.textChanged.connect(lambda text: 
            btn_execute.setEnabled(text.strip() == "确认删除"))
        
        def do_clear():
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("PRAGMA foreign_keys = OFF")
                    
                    if clear_type == "stock_records":
                        cursor.execute("DELETE FROM stock_in")
                        cursor.execute("DELETE FROM stock_out")
                        cursor.execute("UPDATE ingredients SET current_stock = 0")
                        conn.commit()
                        result_msg = "入库出库记录已清理，库存已归零"
                        
                    elif clear_type == "inspection_records":
                        cursor.execute("DELETE FROM inspection_records")
                        conn.commit()
                        result_msg = "进货查验记录已清理"
                        
                    elif clear_type == "check_records":
                        cursor.execute("DELETE FROM inventory_check")
                        conn.commit()
                        result_msg = "库存盘点记录已清理"
                        
                    elif clear_type == "logs":
                        cursor.execute("DELETE FROM operation_logs")
                        conn.commit()
                        result_msg = "操作日志已清理"
                        
                    elif clear_type == "all_business":
                        cursor.execute("DELETE FROM stock_in")
                        cursor.execute("DELETE FROM stock_out")
                        cursor.execute("DELETE FROM inspection_records")
                        cursor.execute("DELETE FROM inventory_check")
                        cursor.execute("DELETE FROM operation_logs")
                        cursor.execute("UPDATE ingredients SET current_stock = 0")
                        conn.commit()
                        result_msg = "所有业务数据已清理，库存已归零"
                        
                    elif clear_type == "all_data":
                        cursor.execute("DELETE FROM stock_in")
                        cursor.execute("DELETE FROM stock_out")
                        cursor.execute("DELETE FROM inspection_records")
                        cursor.execute("DELETE FROM inventory_check")
                        cursor.execute("DELETE FROM operation_logs")
                        cursor.execute("DELETE FROM ingredients")
                        cursor.execute("DELETE FROM suppliers")
                        cursor.execute("DELETE FROM categories")
                        cursor.execute("DELETE FROM category_mappings")
                        cursor.execute("DELETE FROM inspectors")
                        # 保留当前用户，删除其他用户
                        if self.current_user:
                            cursor.execute("DELETE FROM users WHERE id != ?", (self.current_user.id,))
                        else:
                            cursor.execute("DELETE FROM users WHERE id > 1")  # 保留admin
                        conn.commit()
                        result_msg = "系统已重置为初始状态"
                    
                    cursor.execute("PRAGMA foreign_keys = ON")
                    
                    LogDAO.add(self.current_user.id if self.current_user else None, 
                               "数据清理", "system", 0, 
                               f"清理范围: {clear_name}")
                    
                    QMessageBox.information(self, "清理完成", result_msg)
                    confirm_dialog.accept()
                    
            except Exception as e:
                QMessageBox.critical(self, "清理失败", f"操作失败: {str(e)}")
        
        btn_execute.clicked.connect(do_clear)
        btn_cancel.clicked.connect(confirm_dialog.reject)
        
        confirm_dialog.exec()


class ReportExportWidget(QWidget):
    """报表导出页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_export_logs()
        
    def setup_ui(self):
        # 复用主样式表
        self.setStyleSheet(StyleSheet.MAIN_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # 页面标题
        title_section = QVBoxLayout()
        title_label = QLabel("报表导出")
        title_label.setObjectName("page_title")
        subtitle_label = QLabel("选择需要导出的报表和时间范围，一键批量导出")
        subtitle_label.setObjectName("page_subtitle")
        title_section.addWidget(title_label)
        title_section.addWidget(subtitle_label)
        main_layout.addLayout(title_section)
        
        # 时间范围选择
        time_group = QGroupBox("时间范围")
        time_layout = QHBoxLayout(time_group)
        
        time_layout.addWidget(QLabel("年份:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(datetime.now().year)
        self.year_spin.setPrefix("  ")
        self.year_spin.setSuffix(" 年")
        self.year_spin.setFixedWidth(100)
        time_layout.addWidget(self.year_spin)
        
        time_layout.addWidget(QLabel("月份:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(datetime.now().month)
        self.month_spin.setPrefix("  ")
        self.month_spin.setSuffix(" 月")
        self.month_spin.setFixedWidth(90)
        time_layout.addWidget(self.month_spin)
        
        time_layout.addStretch()
        
        tip_label = QLabel("💡 每日出入库、每月汇总按月度统计；财务收支按年度统计；盘存盘亏和进货查验按全部数据导出")
        tip_label.setStyleSheet("color: #86868b; font-size: 12px;")
        time_layout.addWidget(tip_label)
        
        main_layout.addWidget(time_group)
        
        # 报表选择
        report_group = QGroupBox("选择报表")
        report_layout = QVBoxLayout(report_group)
        report_layout.setSpacing(8)
        
        # 全选按钮行
        select_row = QHBoxLayout()
        self.btn_select_all_reports = QPushButton("✅ 全选")
        self.btn_select_all_reports.setObjectName("secondary")
        self.btn_select_all_reports.setFixedWidth(100)
        self.btn_select_all_reports.clicked.connect(self.select_all_reports)
        
        self.btn_unselect_all_reports = QPushButton("❌ 取消全选")
        self.btn_unselect_all_reports.setObjectName("secondary")
        self.btn_unselect_all_reports.setFixedWidth(100)
        self.btn_unselect_all_reports.clicked.connect(self.unselect_all_reports)
        
        self.selected_count_label = QLabel("已选择 0 项")
        self.selected_count_label.setStyleSheet("color: #86868b; font-size: 12px;")
        
        select_row.addWidget(self.btn_select_all_reports)
        select_row.addWidget(self.btn_unselect_all_reports)
        select_row.addWidget(self.selected_count_label)
        select_row.addStretch()
        report_layout.addLayout(select_row)
        
        # 报表列表（2列）
        self.report_checkboxes = []
        reports = [
            ("daily_stock", "📊 每日出入库表", "记录每日食材出入库明细", True),
            ("monthly_summary", "📈 每月汇总表", "月度库存汇总统计", True),
            ("financial", "💰 财务收支表", "采购支出与出库成本统计", True),
            ("inventory_check", "📦 库存盘存盘亏表", "库存盘点差异分析", True),
            ("inspection", "✅ 进货查验记录表", "进货查验记录汇总", True),
        ]
        
        report_grid = QGridLayout()
        report_grid.setSpacing(12)
        
        for i, (key, title, desc, default_checked) in enumerate(reports):
            row = i // 2
            col = i % 2
            
            checkbox = QCheckBox(title)
            checkbox.setProperty("report_key", key)
            if default_checked:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_selected_count)
            checkbox.setStyleSheet("""
                QCheckBox {
                    background-color: #fafafa;
                    border: 1px solid #e5e5ea;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-weight: 500;
                    font-size: 13px;
                }
                QCheckBox:hover {
                    background-color: #f0f0f5;
                    border-color: #0071e3;
                }
            """)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #86868b; font-size: 11px; padding-left: 28px;")
            
            item_layout = QVBoxLayout()
            item_layout.setSpacing(4)
            item_layout.addWidget(checkbox)
            item_layout.addWidget(desc_label)
            
            self.report_checkboxes.append(checkbox)
            report_grid.addLayout(item_layout, row, col)
        
        report_layout.addLayout(report_grid)
        main_layout.addWidget(report_group)
        
        # 导出按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self.btn_export = QPushButton("📤 批量导出选中报表")
        self.btn_export.setObjectName("success")
        self.btn_export.setMinimumWidth(200)
        self.btn_export.setMinimumHeight(44)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.clicked.connect(self.batch_export)
        btn_row.addWidget(self.btn_export)
        
        main_layout.addLayout(btn_row)
        
        # 最近导出记录
        log_group = QGroupBox("最近导出记录")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(8)
        
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()
        self.btn_refresh_log = QPushButton("🔄 刷新记录")
        self.btn_refresh_log.setObjectName("secondary")
        self.btn_refresh_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_log.clicked.connect(self.load_export_logs)
        self.btn_refresh_log.setStyleSheet("""
            QPushButton {
                padding: 6px 14px;
                font-size: 12px;
            }
        """)
        log_btn_layout.addWidget(self.btn_refresh_log)
        log_layout.addLayout(log_btn_layout)
        
        self.export_log_table = QTableWidget()
        self.export_log_table.setColumnCount(2)
        self.export_log_table.setHorizontalHeaderLabels(["时间", "操作内容"])
        self.export_log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.export_log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.export_log_table.verticalHeader().setVisible(False)
        self.export_log_table.setAlternatingRowColors(True)
        self.export_log_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.export_log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.export_log_table.setMaximumHeight(150)
        log_layout.addWidget(self.export_log_table)
        
        main_layout.addWidget(log_group)
        main_layout.addStretch()
        
        self.update_selected_count()

    def load_export_logs(self):
        logs = LogDAO.get_by_action_keyword("导出", 10)
        self.export_log_table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self.export_log_table.setItem(i, 0, QTableWidgetItem(log.created_at))
            action_text = log.action
            if log.details:
                action_text += f" - {log.details}"
            self.export_log_table.setItem(i, 1, QTableWidgetItem(action_text))
    
    def select_all_reports(self):
        for cb in self.report_checkboxes:
            cb.setChecked(True)
    
    def unselect_all_reports(self):
        for cb in self.report_checkboxes:
            cb.setChecked(False)
    
    def update_selected_count(self):
        count = sum(1 for cb in self.report_checkboxes if cb.isChecked())
        self.selected_count_label.setText(f"已选择 {count} 项")
    
    def batch_export(self):
        year = self.year_spin.value()
        month = self.month_spin.value()
        selected = [cb.property("report_key") for cb in self.report_checkboxes if cb.isChecked()]
        
        if not selected:
            QMessageBox.warning(self, "提示", "请至少选择一个报表")
            return
        
        output_dir = QFileDialog.getExistingDirectory(self, "选择导出目录", "")
        if not output_dir:
            return
        
        success_count = 0
        fail_count = 0
        results = []
        
        report_map = {
            "daily_stock": ("每日出入库表", f"{output_dir}/每日出入库表_{year}年{month}月.xlsx", lambda path: ReportGenerator.export_daily_stock_sheet(self, year, month, path), f"{year}年{month}月"),
            "monthly_summary": ("每月汇总表", f"{output_dir}/每月出入库统计表_{year}年{month}月.xlsx", lambda path: ReportGenerator.export_monthly_summary(self, year, month, path), f"{year}年{month}月"),
            "financial": ("财务收支表", f"{output_dir}/财务收支情况表_{year}年度.xlsx", lambda path: ReportGenerator.export_financial_report(self, year, path), f"{year}年度"),
            "inventory_check": ("库存盘存盘亏表", f"{output_dir}/库存物品盘存盘亏表_{datetime.now().strftime('%Y%m%d')}.xlsx", lambda path: ReportGenerator.export_inventory_check_sheet(self, path), ""),
            "inspection": ("进货查验记录表", f"{output_dir}/进货查验记录表_{datetime.now().strftime('%Y%m%d')}.xlsx", lambda path: ReportGenerator.export_inspection_report(self, path), ""),
        }
        
        for key in selected:
            if key in report_map:
                name, file_path, func, detail = report_map[key]
                try:
                    if func(file_path):
                        success_count += 1
                        results.append(f"✅ {name}")
                        LogDAO.add(None, f"导出{name}", "export", 0, detail)
                    else:
                        fail_count += 1
                        results.append(f"❌ {name}")
                except Exception as e:
                    fail_count += 1
                    results.append(f"❌ {name} - {str(e)}")
        
        self.load_export_logs()
        
        msg = f"批量导出完成！\n\n成功: {success_count} 个\n失败: {fail_count} 个\n\n" + "\n".join(results)
        if fail_count == 0:
            QMessageBox.information(self, "导出成功", msg)
        else:
            QMessageBox.warning(self, "导出完成", msg)


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        logger.info(f"主窗口初始化开始，当前用户: {current_user.username if current_user else 'None'}")
        
        self.setWindowTitle("学校食堂食材管理系统")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)
        
        # 设置窗口图标（使用兼容路径）
        self.icon_path = get_resource_path('app_icon.ico')
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))
            logger.info(f"窗口图标已设置: {self.icon_path}")
        else:
            logger.warning(f"图标文件不存在: {self.icon_path}")
        
        try:
            self.setup_ui()
            logger.info("主窗口UI初始化完成")
        except Exception as e:
            logger.error(f"主窗口UI初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise
        
        self.showMaximized()
        logger.info("主窗口已显示")
        
    def setup_ui(self):
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左侧导航栏 - macOS 风格
        nav_widget = QWidget()
        nav_widget.setMaximumWidth(220)
        nav_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f7;
                border-right: 1px solid #d2d2d7;
            }
            QPushButton {
                background-color: transparent;
                color: #1d1d1f;
                border: none;
                padding: 12px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: 400;
                border-radius: 8px;
                margin: 2px 10px;
            }
            QPushButton:hover {
                background-color: #e8e8ed;
            }
            QPushButton:checked {
                background-color: #0071e3;
                color: white;
                font-weight: 500;
            }
        """)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 16, 0, 16)
        nav_layout.setSpacing(4)
        
        # 标题区域（带图标）
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(16, 8, 16, 8)
        title_layout.setSpacing(10)
        
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setScaledContents(True)
        if os.path.exists(self.icon_path):
            icon_label.setPixmap(QIcon(self.icon_path).pixmap(32, 32))
        title_layout.addWidget(icon_label)
        
        title = QLabel("食堂食材管理")
        title.setStyleSheet("color: #1d1d1f; font-size: 18px; font-weight: 700;")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        nav_layout.addWidget(title_widget)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #d2d2d7; margin: 0 16px;")
        nav_layout.addWidget(line)
        
        nav_layout.addSpacing(12)
        
        # 导航按钮
        self.nav_buttons = []
        nav_items = [
            ("概览统计", self.show_overview),
            ("提醒中心", self.show_alerts),
            ("财务统计", self.show_finance),
            ("食材管理", self.show_ingredients),
            ("入库管理", self.show_stock_in),
            ("出库管理", self.show_stock_out),
            ("库存盘点", self.show_inventory),
            ("进货查验", self.show_inspection),
            ("报表导出", self.show_reports),
            ("供应商管理", self.show_suppliers),
            ("分类管理", self.show_categories),
            ("类别映射", self.show_category_mapping),
            ("系统设置", self.show_settings),
        ]
        
        for text, handler in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(handler)
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        nav_layout.addStretch()
        
        # 版本信息
        version = QLabel("v1.0.1")
        version.setStyleSheet("color: #86868b; padding: 10px; font-size: 12px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(version)
        
        layout.addWidget(nav_widget)
        
        # 右侧内容区
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #f5f5f7;")
        layout.addWidget(self.stack, 1)
        
        # 创建各个页面
        self.overview_page = ReportWidget()
        self.alert_page = AlertWidget()
        self.finance_page = FinanceWidget()
        self.ingredient_dialog = IngredientDialog()
        self.stock_in_dialog = StockInDialog()
        self.stock_out_dialog = StockOutDialog()
        self.inventory_dialog = InventoryCheckDialog()
        self.inspection_dialog = InspectionRecordDialog()
        self.report_export_page = ReportExportWidget()
        self.supplier_dialog = SupplierDialog()
        self.category_dialog = CategoryDialog()
        self.category_mapping_dialog = CategoryMappingDialog()
        self.settings_page = SettingsWidget(current_user=self.current_user)
        
        self.stack.addWidget(self.overview_page)
        self.stack.addWidget(self.alert_page)
        self.stack.addWidget(self.finance_page)
        self.stack.addWidget(self.ingredient_dialog)
        self.stack.addWidget(self.stock_in_dialog)
        self.stack.addWidget(self.stock_out_dialog)
        self.stack.addWidget(self.inventory_dialog)
        self.stack.addWidget(self.inspection_dialog)
        self.stack.addWidget(self.report_export_page)
        self.stack.addWidget(self.supplier_dialog)
        self.stack.addWidget(self.category_dialog)
        self.stack.addWidget(self.category_mapping_dialog)
        self.stack.addWidget(self.settings_page)
        
        # 默认选中第一个
        self.nav_buttons[0].setChecked(True)
        
        # 状态栏
        self.statusBar().showMessage("系统就绪")
        
    def show_overview(self):
        self.stack.setCurrentIndex(0)
        self.overview_page.load_data()
        self.update_nav(0)
        
    def show_alerts(self):
        self.stack.setCurrentIndex(1)
        self.alert_page.load_data()
        self.update_nav(1)
        
    def show_finance(self):
        self.stack.setCurrentIndex(2)
        self.finance_page.load_data()
        self.update_nav(2)
        
    def show_ingredients(self):
        self.stack.setCurrentIndex(3)
        self.ingredient_dialog.load_data()
        self.update_nav(3)
        
    def show_stock_in(self):
        self.stack.setCurrentIndex(4)
        self.stock_in_dialog.load_data()
        self.stock_in_dialog.load_ingredients()
        self.update_nav(4)
        
    def show_stock_out(self):
        self.stack.setCurrentIndex(5)
        self.stock_out_dialog.load_data()
        self.stock_out_dialog.load_ingredients()
        self.update_nav(5)
        
    def show_inventory(self):
        self.stack.setCurrentIndex(6)
        self.inventory_dialog.load_data()
        self.inventory_dialog.load_ingredients()
        self.update_nav(6)
        
    def show_inspection(self):
        self.stack.setCurrentIndex(7)
        self.inspection_dialog.load_data()
        self.update_nav(7)
        
    def show_reports(self):
        self.stack.setCurrentIndex(8)
        self.update_nav(8)
        
    def show_suppliers(self):
        self.stack.setCurrentIndex(9)
        self.supplier_dialog.load_data()
        self.update_nav(9)
        
    def show_categories(self):
        self.stack.setCurrentIndex(10)
        self.category_dialog.load_data()
        self.update_nav(10)
        
    def show_category_mapping(self):
        self.stack.setCurrentIndex(11)
        self.category_mapping_dialog.load_data()
        self.update_nav(11)
        
    def show_settings(self):
        self.stack.setCurrentIndex(12)
        self.update_nav(12)
        
    def update_nav(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)


def main():
    logger.info("=" * 50)
    logger.info("程序启动")
    logger.info(f"工作目录: {os.path.dirname(os.path.abspath(__file__))}")
    logger.info(f"Python版本: {sys.version}")
    
    try:
        # 初始化数据库
        logger.info("正在初始化数据库...")
        init_database()
        logger.info("数据库初始化完成")
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        logger.info("QApplication创建完成")
        
        # 设置应用字体
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)
        
        # 设置应用图标
        icon_path = get_resource_path('app_icon.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            logger.info(f"应用图标已设置: {icon_path}")
        
        # 显示登录对话框
        logger.info("显示登录对话框...")
        login = LoginDialog()
        result = login.exec()
        logger.info(f"登录对话框结果: {result}")
        
        if result != QDialog.DialogCode.Accepted:
            logger.info("用户取消登录，程序退出")
            sys.exit(0)
        
        logger.info("创建主窗口...")
        window = MainWindow(current_user=login.current_user)
        window.show()
        logger.info("进入主事件循环")
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"程序发生严重错误: {e}")
        logger.critical(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
