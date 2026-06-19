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
                             QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor

from database import (init_database, DB_PATH, UserDAO, CategoryDAO, SupplierDAO, IngredientDAO,
                      StockInDAO, StockOutDAO, InventoryCheckDAO, ReportDAO, LogDAO)
from excel_handler import ExcelHandler


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
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
            padding: 8px 12px;
            border: 1px solid #d2d2d7;
            border-radius: 8px;
            background-color: white;
            font-size: 13px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #0071e3;
        }
        QComboBox::drop-down {
            border: none;
            width: 24px;
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
    """


class BaseDialog(QDialog):
    """基础对话框"""
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)
        
    def show_error(self, message):
        QMessageBox.critical(self, "错误", message)
    
    def show_info(self, message):
        QMessageBox.information(self, "提示", message)
    
    def confirm(self, message):
        reply = QMessageBox.question(self, "确认", message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes


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


class SupplierDialog(BaseDialog):
    """供应商管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "供应商管理")
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "供应商名称", "联系人", "电话", "地址", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加供应商")
        self.btn_add.setObjectName("success")
        self.btn_edit = QPushButton("编辑")
        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("danger")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
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
    
    def add_supplier(self):
        dialog = SupplierEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            sid = SupplierDAO.add(**data)
            self.show_info("添加成功")
            LogDAO.add(None, "添加供应商", "supplier", sid, f"供应商: {data['name']}")
            self.load_data()
    
    def edit_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要编辑的供应商")
            return
        
        supplier_id = int(self.table.item(row, 0).text())
        dialog = SupplierEditDialog(self, supplier_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            SupplierDAO.update(supplier_id, **data)
            self.show_info("更新成功")
            LogDAO.add(None, "编辑供应商", "supplier", supplier_id, f"供应商: {data['name']}")
            self.load_data()
    
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
        
        self.name_edit = QLineEdit()
        self.contact_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.email_edit = QLineEdit()
        
        layout.addRow("供应商名称*:", self.name_edit)
        layout.addRow("联系人:", self.contact_edit)
        layout.addRow("电话:", self.phone_edit)
        layout.addRow("地址:", self.address_edit)
        layout.addRow("邮箱:", self.email_edit)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_save.setObjectName("success")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)
        
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
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索食材名称...")
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.search)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材名称", "分类", "规格", "单位", "当前库存", "安全库存", "供应商"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加食材")
        self.btn_add.setObjectName("success")
        self.btn_edit = QPushButton("编辑")
        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("danger")
        self.btn_import = QPushButton("导入Excel")
        self.btn_import.setObjectName("warning")
        self.btn_export = QPushButton("导出余量")
        self.btn_export.setObjectName("success")
        self.btn_template = QPushButton("下载模板")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_template)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
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
        filtered = [ing for ing in ingredients if keyword in ing.name.lower()]
        
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
            iid = IngredientDAO.add(**data)
            self.show_info("添加成功")
            LogDAO.add(None, "添加食材", "ingredient", iid, f"食材: {data['name']}")
            self.load_data()
    
    def edit_ingredient(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("请选择要编辑的食材")
            return
        
        ingredient_id = int(self.table.item(row, 0).text())
        dialog = IngredientEditDialog(self, ingredient_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            IngredientDAO.update(ingredient_id, **data)
            self.show_info("更新成功")
            LogDAO.add(None, "编辑食材", "ingredient", ingredient_id, f"食材: {data['name']}")
            self.load_data()
    
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
                self.show_error("删除失败")
    
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
        
        layout.addRow("食材名称*:", self.name_edit)
        layout.addRow("分类*:", self.category_combo)
        layout.addRow("单位*:", self.unit_edit)
        layout.addRow("规格:", self.spec_edit)
        layout.addRow("安全库存:", self.safety_stock_spin)
        layout.addRow("供应商:", self.supplier_combo)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_save.setObjectName("success")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)
        
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
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_group = QGroupBox("新增入库")
        form_layout = QFormLayout(form_group)
        
        self.ingredient_combo = QComboBox()
        self.load_ingredients()
        
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(999999)
        self.quantity_spin.setValue(1)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        self.price_spin.setPrefix("¥ ")
        
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- 请选择 --", None)
        suppliers = SupplierDAO.get_active()
        for s in suppliers:
            self.supplier_combo.addItem(s.name, s.id)
        
        self.batch_edit = QLineEdit()
        self.production_date = QDateEdit()
        self.production_date.setCalendarPopup(True)
        self.production_date.setDate(QDate.currentDate())
        
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addDays(30))
        
        self.operator_edit = QLineEdit()
        self.remark_edit = QLineEdit()
        
        form_layout.addRow("食材*:", self.ingredient_combo)
        form_layout.addRow("数量*:", self.quantity_spin)
        form_layout.addRow("单价*:", self.price_spin)
        form_layout.addRow("供应商:", self.supplier_combo)
        form_layout.addRow("批次号:", self.batch_edit)
        form_layout.addRow("生产日期:", self.production_date)
        form_layout.addRow("保质期至:", self.expiry_date)
        form_layout.addRow("操作人:", self.operator_edit)
        form_layout.addRow("备注:", self.remark_edit)
        
        self.btn_in = QPushButton("确认入库")
        self.btn_in.setObjectName("success")
        form_layout.addRow(self.btn_in)
        
        layout.addWidget(form_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材", "数量", "单价", "总价", "供应商", "操作人", "入库时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("近期入库记录:"))
        layout.addWidget(self.table)
        
        self.btn_in.clicked.connect(self.do_stock_in)
        
    def load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = IngredientDAO.get_all()
        for ing in ingredients:
            self.ingredient_combo.addItem(f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id)
    
    def load_data(self):
        records = StockInDAO.get_all()
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
    
    def do_stock_in(self):
        ingredient_id = self.ingredient_combo.currentData()
        quantity = self.quantity_spin.value()
        price = self.price_spin.value()
        
        if not ingredient_id or quantity <= 0 or price < 0:
            self.show_error("请填写完整的入库信息")
            return
        
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


class StockOutDialog(BaseDialog):
    """出库管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "出库管理")
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_group = QGroupBox("新增出库")
        form_layout = QFormLayout(form_group)
        
        self.ingredient_combo = QComboBox()
        self.load_ingredients()
        
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(999999)
        self.quantity_spin.setValue(1)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        self.price_spin.setPrefix("¥ ")
        
        self.purpose_edit = QLineEdit()
        self.department_edit = QLineEdit()
        self.operator_edit = QLineEdit()
        self.remark_edit = QLineEdit()
        
        form_layout.addRow("食材*:", self.ingredient_combo)
        form_layout.addRow("数量*:", self.quantity_spin)
        form_layout.addRow("单价:", self.price_spin)
        form_layout.addRow("用途:", self.purpose_edit)
        form_layout.addRow("领用部门:", self.department_edit)
        form_layout.addRow("操作人:", self.operator_edit)
        form_layout.addRow("备注:", self.remark_edit)
        
        self.btn_out = QPushButton("确认出库")
        self.btn_out.setObjectName("warning")
        form_layout.addRow(self.btn_out)
        
        layout.addWidget(form_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材", "数量", "用途", "领用部门", "操作人", "备注", "出库时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("近期出库记录:"))
        layout.addWidget(self.table)
        
        self.btn_out.clicked.connect(self.do_stock_out)
        
    def load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = IngredientDAO.get_all()
        for ing in ingredients:
            self.ingredient_combo.addItem(
                f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id
            )
    
    def load_data(self):
        records = StockOutDAO.get_all()
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
    
    def do_stock_out(self):
        ingredient_id = self.ingredient_combo.currentData()
        quantity = self.quantity_spin.value()
        
        if not ingredient_id or quantity <= 0:
            self.show_error("请填写完整的出库信息")
            return
        
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


class InventoryCheckDialog(BaseDialog):
    """库存盘点对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, "库存盘点")
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 盘点表单
        form_group = QGroupBox("新增盘点")
        form_layout = QFormLayout(form_group)
        
        self.ingredient_combo = QComboBox()
        self.load_ingredients()
        
        self.system_stock_label = QLabel("-")
        self.actual_stock_spin = QDoubleSpinBox()
        self.actual_stock_spin.setMaximum(999999)
        self.actual_stock_spin.setValue(0)
        
        self.operator_edit = QLineEdit()
        self.remark_edit = QLineEdit()
        
        form_layout.addRow("食材*:", self.ingredient_combo)
        form_layout.addRow("系统库存:", self.system_stock_label)
        form_layout.addRow("实际库存*:", self.actual_stock_spin)
        form_layout.addRow("盘点人:", self.operator_edit)
        form_layout.addRow("备注:", self.remark_edit)
        
        self.btn_check = QPushButton("确认盘点")
        self.btn_check.setObjectName("success")
        form_layout.addRow(self.btn_check)
        
        layout.addWidget(form_group)
        
        # 盘点记录
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材", "系统库存", "实际库存", "差异", "盘点人", "时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("盘点记录:"))
        layout.addWidget(self.table)
        
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
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 数据备份
        group1 = QGroupBox("数据备份与恢复")
        g1_layout = QVBoxLayout(group1)
        
        backup_layout = QHBoxLayout()
        self.btn_backup = QPushButton("备份数据")
        self.btn_backup.setObjectName("success")
        self.btn_backup.clicked.connect(self.backup_data)
        
        self.btn_restore = QPushButton("恢复数据")
        self.btn_restore.setObjectName("warning")
        self.btn_restore.clicked.connect(self.restore_data)
        
        backup_layout.addWidget(self.btn_backup)
        backup_layout.addWidget(self.btn_restore)
        backup_layout.addStretch()
        g1_layout.addLayout(backup_layout)
        
        layout.addWidget(group1)
        
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
        
        self.btn_change_pwd = QPushButton("修改密码")
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
            ("供应商管理", self.show_suppliers),
            ("分类管理", self.show_categories),
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
        version = QLabel("v2.0.0")
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
        self.supplier_dialog = SupplierDialog()
        self.category_dialog = CategoryDialog()
        self.settings_page = SettingsWidget(current_user=self.current_user)
        
        self.stack.addWidget(self.overview_page)
        self.stack.addWidget(self.alert_page)
        self.stack.addWidget(self.finance_page)
        self.stack.addWidget(self.ingredient_dialog)
        self.stack.addWidget(self.stock_in_dialog)
        self.stack.addWidget(self.stock_out_dialog)
        self.stack.addWidget(self.inventory_dialog)
        self.stack.addWidget(self.supplier_dialog)
        self.stack.addWidget(self.category_dialog)
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
        
    def show_suppliers(self):
        self.stack.setCurrentIndex(7)
        self.supplier_dialog.load_data()
        self.update_nav(7)
        
    def show_categories(self):
        self.stack.setCurrentIndex(8)
        self.category_dialog.load_data()
        self.update_nav(8)
        
    def show_settings(self):
        self.stack.setCurrentIndex(9)
        self.update_nav(9)
        
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
