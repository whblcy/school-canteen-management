"""
系统设置视图 - 数据管理、查验人员、密码修改、数据清理、操作日志
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton, QLabel,
    QGroupBox, QLineEdit, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup,
    QAbstractItemView,
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ..base_dialog import BaseDialog
from ...config import get_config

cfg = get_config()
ui = cfg.ui


class InspectorEditDialog(BaseDialog):
    """查验人员编辑/新增对话框"""

    def __init__(self, inspector=None, parent=None):
        title = "编辑查验人" if inspector else "新增查验人"
        super().__init__(parent, title)
        self.inspector = inspector
        self._setup_ui()
        if inspector is not None:
            self._load_data()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(ui.operation_spacing)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入姓名")

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("请输入联系电话")

        self.dept_edit = QLineEdit()
        self.dept_edit.setPlaceholderText("请输入所属部门")

        for w in [self.name_edit, self.phone_edit, self.dept_edit]:
            self.setup_form_field(w)

        layout.addRow("姓名*:", self.name_edit)
        layout.addRow("电话:", self.phone_edit)
        layout.addRow("部门:", self.dept_edit)

        self.btn_save = self.make_button("保存", css_class="success")
        self.btn_cancel = self.make_button("取消", css_class="secondary")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addRow("", self.create_button_layout(self.btn_save, self.btn_cancel))

    def _load_data(self):
        insp = self.inspector
        self.name_edit.setText(insp.name or "")
        self.phone_edit.setText(insp.phone or "")
        self.dept_edit.setText(insp.department or "")

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "department": self.dept_edit.text().strip(),
        }


class SettingsView(BasePage):
    """系统设置页面"""

    data_cleared = pyqtSignal()

    def __init__(self, data_mgmt_service, inspector_service, auth_service,
                 title, current_user=None, parent=None):
        self.data_mgmt_service = data_mgmt_service
        self.inspector_service = inspector_service
        self.auth_service = auth_service
        self.current_user = current_user
        # 尝试构造日志服务
        self.log_service = None
        try:
            log_repo = getattr(data_mgmt_service, "log_repo", None)
            if log_repo is not None:
                from ...services.utility_services import LogService
                self.log_service = LogService(log_repo)
        except Exception:
            self.log_service = None
        super().__init__(title, parent)
        self._setup_ui()
        self._load_inspectors()
        self._load_logs()

    def _setup_ui(self):
        # ===== Section 1: 数据管理 =====
        group_backup = QGroupBox("数据管理")
        backup_layout = QHBoxLayout(group_backup)
        backup_layout.setSpacing(ui.button_spacing)

        self.btn_backup = QPushButton("数据备份")
        apply_css_class(self.btn_backup, "success")
        self.btn_backup.clicked.connect(self._backup_data)
        backup_layout.addWidget(self.btn_backup)

        self.btn_restore = QPushButton("数据恢复")
        apply_css_class(self.btn_restore, "warning")
        self.btn_restore.clicked.connect(self._restore_data)
        backup_layout.addWidget(self.btn_restore)

        backup_layout.addStretch()
        self.add_widget(group_backup)

        # ===== Section 2: 查验人员管理 =====
        group_insp = QGroupBox("查验人员管理")
        insp_layout = QVBoxLayout(group_insp)
        insp_layout.setSpacing(ui.operation_spacing)

        insp_btn_row = QHBoxLayout()
        self.btn_insp_add = QPushButton("新增查验人")
        apply_css_class(self.btn_insp_add, "primary")
        self.btn_insp_add.clicked.connect(self._add_inspector)
        insp_btn_row.addWidget(self.btn_insp_add)
        insp_btn_row.addStretch()
        insp_layout.addLayout(insp_btn_row)

        self.inspector_table = QTableWidget()
        self.inspector_table.setColumnCount(6)
        self.inspector_table.setHorizontalHeaderLabels([
            "ID", "姓名", "电话", "部门", "状态", "操作",
        ])
        self.inspector_table.setColumnHidden(0, True)
        self.inspector_table.setColumnWidth(4, 60)
        self.inspector_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.inspector_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self.inspector_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)
        self.inspector_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents)
        self.inspector_table.setAlternatingRowColors(True)
        self.inspector_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.inspector_table.verticalHeader().setVisible(False)
        self.inspector_table.setMaximumHeight(220)
        insp_layout.addWidget(self.inspector_table)

        self.add_widget(group_insp)

        # ===== Section 3: 修改密码 =====
        group_pwd = QGroupBox("修改密码")
        pwd_layout = QFormLayout(group_pwd)
        pwd_layout.setSpacing(ui.operation_spacing)

        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)

        for w in [self.old_pwd, self.new_pwd, self.confirm_pwd]:
            w.setMinimumWidth(ui.form_field_min_width)

        pwd_layout.addRow("原密码:", self.old_pwd)
        pwd_layout.addRow("新密码:", self.new_pwd)
        pwd_layout.addRow("确认新密码:", self.confirm_pwd)

        self.btn_change_pwd = QPushButton("修改密码")
        apply_css_class(self.btn_change_pwd, "success")
        self.btn_change_pwd.clicked.connect(self._change_password)
        pwd_layout.addRow("", self._wrap_right(self.btn_change_pwd))

        self.add_widget(group_pwd)

        # ===== Section 4: 数据清理（危险操作） =====
        group_clear = QGroupBox("⚠️ 数据清理（危险操作）")
        group_clear.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                border: 2px solid {ui.color_red};
                border-radius: 12px;
                margin-top: 12px;
                padding: 16px;
                background-color: #fff5f5;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: {ui.color_red};
                font-size: 14px;
            }}
        """)
        clear_layout = QVBoxLayout(group_clear)
        clear_layout.setSpacing(ui.operation_spacing)

        # 单选按钮
        radio_row = QHBoxLayout()
        radio_row.addWidget(QLabel("清理范围:"))

        self.clear_radio_group = QButtonGroup(self)
        self.radio_stock = QRadioButton("清理出入库记录")
        self.radio_inventory = QRadioButton("清理盘点记录")
        self.radio_all = QRadioButton("清理全部业务数据")
        self.radio_stock.setChecked(True)

        self.clear_radio_group.addButton(self.radio_stock, 0)
        self.clear_radio_group.addButton(self.radio_inventory, 1)
        self.clear_radio_group.addButton(self.radio_all, 2)

        radio_row.addWidget(self.radio_stock)
        radio_row.addWidget(self.radio_inventory)
        radio_row.addWidget(self.radio_all)
        radio_row.addStretch()
        clear_layout.addLayout(radio_row)

        # 风险提示
        risk_label = QLabel(
            "⚠️ <b>风险提示：</b><br>"
            "• 删除的数据<b>无法恢复</b>，请务必先备份！<br>"
            "• 清理出入库记录将导致库存数据归零<br>"
            "• 清理全部业务数据将重置为初始状态"
        )
        risk_label.setStyleSheet(
            f"color: {ui.color_text_secondary}; font-size: 12px; "
            "padding: 10px; background: #fff; border-radius: 6px;")
        risk_label.setWordWrap(True)
        clear_layout.addWidget(risk_label)

        # 清理按钮
        clear_btn_row = QHBoxLayout()
        clear_btn_row.addStretch()
        self.btn_clear_data = QPushButton("执行清理")
        apply_css_class(self.btn_clear_data, "danger")
        self.btn_clear_data.setMinimumWidth(120)
        self.btn_clear_data.clicked.connect(self._clear_data)
        clear_btn_row.addWidget(self.btn_clear_data)
        clear_layout.addLayout(clear_btn_row)

        self.add_widget(group_clear)

        # ===== Section 5: 操作日志（可折叠） =====
        group_log = QGroupBox("操作日志")
        group_log.setCheckable(True)
        group_log.setChecked(False)
        group_log.toggled.connect(self._on_log_group_toggled)
        log_layout = QVBoxLayout(group_log)
        log_layout.setSpacing(ui.operation_spacing)

        log_btn_row = QHBoxLayout()
        log_btn_row.addStretch()
        self.btn_refresh_log = QPushButton("刷新")
        apply_css_class(self.btn_refresh_log, "secondary")
        self.btn_refresh_log.setFixedWidth(80)
        self.btn_refresh_log.clicked.connect(self._load_logs)
        log_btn_row.addWidget(self.btn_refresh_log)
        log_layout.addLayout(log_btn_row)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["时间", "操作人", "操作", "详情"])
        self.log_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setMaximumHeight(180)
        log_layout.addWidget(self.log_table)

        self.add_widget(group_log)

        self.content_layout.addStretch()

    def _wrap_right(self, widget) -> QWidget:
        """将按钮包装在右对齐的容器中"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(widget)
        return container

    def _on_log_group_toggled(self, checked):
        self.log_table.setVisible(checked)
        self.btn_refresh_log.setVisible(checked)
        if checked:
            self._load_logs()

    # ===== Section 1: 数据管理 =====

    def _backup_data(self):
        try:
            file_path = self.data_mgmt_service.backup_database(self)
            if file_path:
                QMessageBox.information(
                    self, "备份成功", f"数据已备份到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", str(e))

    def _restore_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", "", "Database Files (*.db)")
        if not file_path:
            return
        reply = QMessageBox.question(
            self, "确认恢复",
            "恢复数据将覆盖当前所有数据，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.data_mgmt_service.restore_database(file_path, self)
            QMessageBox.information(self, "恢复成功", "数据已恢复，请重启程序")
            self.data_cleared.emit()
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", str(e))

    # ===== Section 2: 查验人员管理 =====

    def _load_inspectors(self):
        try:
            inspectors = self.inspector_service.get_all()
        except Exception:
            inspectors = []

        self.inspector_table.setRowCount(len(inspectors))
        for i, insp in enumerate(inspectors):
            self.inspector_table.setItem(i, 0, QTableWidgetItem(str(insp.id)))
            self.inspector_table.setItem(i, 1, QTableWidgetItem(insp.name or ""))
            self.inspector_table.setItem(i, 2, QTableWidgetItem(insp.phone or ""))
            self.inspector_table.setItem(i, 3, QTableWidgetItem(insp.department or ""))

            status_item = QTableWidgetItem()
            if insp.status == 1:
                status_item.setText("启用")
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setText("停用")
                status_item.setForeground(Qt.GlobalColor.red)
            self.inspector_table.setItem(i, 4, status_item)

            self.inspector_table.setCellWidget(
                i, 5, self._create_inspector_operation_widget(insp.id))

    def _create_inspector_operation_widget(self, inspector_id: int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        btn_edit = QPushButton("编辑")
        apply_css_class(btn_edit, "secondary")
        btn_edit.setFixedWidth(50)
        btn_edit.clicked.connect(
            lambda _, iid=inspector_id: self._edit_inspector(iid))

        btn_delete = QPushButton("删除")
        apply_css_class(btn_delete, "danger")
        btn_delete.setFixedWidth(50)
        btn_delete.clicked.connect(
            lambda _, iid=inspector_id: self._delete_inspector(iid))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        return widget

    def _add_inspector(self):
        dialog = InspectorEditDialog(parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "姓名不能为空")
            return
        try:
            self.inspector_service.create(**data)
            QMessageBox.information(self, "成功", "添加查验人成功")
            self._load_inspectors()
        except Exception as e:
            QMessageBox.critical(self, "添加失败", str(e))

    def _edit_inspector(self, inspector_id: int):
        # 从表格获取当前查验人对象
        inspector = None
        try:
            all_inspectors = self.inspector_service.get_all()
            inspector = next(
                (i for i in all_inspectors if i.id == inspector_id), None)
        except Exception:
            pass
        if inspector is None:
            QMessageBox.warning(self, "错误", "未找到查验人信息")
            return

        dialog = InspectorEditDialog(inspector=inspector, parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "提示", "姓名不能为空")
            return
        try:
            self.inspector_service.update(inspector_id, **data)
            QMessageBox.information(self, "成功", "更新查验人成功")
            self._load_inspectors()
        except Exception as e:
            QMessageBox.critical(self, "更新失败", str(e))

    def _delete_inspector(self, inspector_id: int):
        name = ""
        try:
            all_inspectors = self.inspector_service.get_all()
            for i in all_inspectors:
                if i.id == inspector_id:
                    name = i.name or ""
                    break
        except Exception:
            pass

        reply = QMessageBox.question(
            self, "确认删除", f"确定删除查验人「{name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.inspector_service.delete(inspector_id)
            QMessageBox.information(self, "成功", "删除成功")
            self._load_inspectors()
        except Exception as e:
            QMessageBox.critical(self, "删除失败", str(e))

    # ===== Section 3: 修改密码 =====

    def _change_password(self):
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

        try:
            self.auth_service.change_password(
                self.current_user.id, old, new_pwd)
            QMessageBox.information(self, "成功", "密码修改成功，请牢记新密码")
            self.old_pwd.clear()
            self.new_pwd.clear()
            self.confirm_pwd.clear()
        except Exception as e:
            QMessageBox.critical(self, "修改失败", str(e))

    # ===== Section 4: 数据清理 =====

    def _clear_data(self):
        # 确定清理模式
        if self.radio_stock.isChecked():
            mode = "stock_records"
            mode_name = "清理出入库记录"
            risk_desc = (
                "<b>即将删除以下数据：</b><br>"
                "• 所有入库记录<br>"
                "• 所有出库记录<br><br>"
                "<b>后果：</b><br>"
                "• 所有食材库存将变为 0<br>"
                "• 出入库历史记录全部丢失<br>"
                "• 相关财务统计报表将无数据"
            )
        elif self.radio_inventory.isChecked():
            mode = "inventory"
            mode_name = "清理盘点记录"
            risk_desc = (
                "<b>即将删除以下数据：</b><br>"
                "• 所有库存盘点记录<br><br>"
                "<b>后果：</b><br>"
                "• 盘点历史记录全部丢失<br>"
                "• 库存将重置为 0"
            )
        else:
            mode = "all_data"
            mode_name = "清理全部业务数据"
            risk_desc = (
                "<b>即将删除以下数据：</b><br>"
                "• 所有出入库记录<br>"
                "• 所有查验记录<br>"
                "• 所有盘点记录<br>"
                "• 库存数据重置<br><br>"
                "<b>后果：</b><br>"
                "• 系统将恢复为初始状态<br>"
                "• 仅保留食材、供应商、分类等基础数据"
            )

        # Step 1: 警告对话框
        reply = QMessageBox.warning(
            self, f"危险操作 - {mode_name}",
            f"⚠️ {risk_desc}<br><br><b>此操作不可逆，请确认已备份！</b>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Step 2: 输入确认文字
        helper = BaseDialog(self)
        confirmed = helper.confirm_with_input(
            f"你正在执行「{mode_name}」操作。\n"
            "此操作将永久删除相关数据且无法恢复！",
            cfg.business.confirm_delete_phrase,
        )
        if not confirmed:
            return

        # 执行清理
        try:
            self.data_mgmt_service.clear_data(
                mode, cfg.business.confirm_delete_phrase)
            QMessageBox.information(self, "清理完成", f"{mode_name}已完成")
            self.data_cleared.emit()
        except Exception as e:
            QMessageBox.critical(self, "清理失败", str(e))

    # ===== Section 5: 操作日志 =====

    def _load_logs(self):
        if not self.log_service:
            self.log_table.setRowCount(0)
            return
        try:
            logs = self.log_service.get_all(20)
        except Exception:
            self.log_table.setRowCount(0)
            return

        self.log_table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self.log_table.setItem(
                i, 0, QTableWidgetItem(str(log.created_at or "")))
            user_name = "系统"
            if log.user:
                user_name = getattr(log.user, "real_name", None) \
                    or getattr(log.user, "username", None) or "系统"
            self.log_table.setItem(i, 1, QTableWidgetItem(user_name))
            self.log_table.setItem(
                i, 2, QTableWidgetItem(log.action or ""))
            self.log_table.setItem(
                i, 3, QTableWidgetItem(log.details or ""))

    # ===== 刷新 =====

    def refresh(self):
        self._load_inspectors()
        self._load_logs()

    def on_show(self):
        pass
