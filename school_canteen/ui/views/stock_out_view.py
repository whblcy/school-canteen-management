"""
出库管理页面 - 食材出库登记、批量出库、记录导出
"""
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
    QLineEdit, QLabel, QGroupBox, QHeaderView, QMessageBox,
    QDateTimeEdit,
)
from PyQt6.QtCore import Qt, QDateTime
from peewee import fn, SQL

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ...config import get_config
from ...core.session import Session
from ...core.exceptions import (
    NotFoundError, ValidationError, BusinessRuleError,
    InsufficientStockError, ExpiredIngredientError,
)

cfg = get_config()
ui = cfg.ui


class StockOutView(BasePage):
    """出库管理页面"""

    def __init__(self, stock_service, ingredient_service, title, parent=None):
        self.stock_service = stock_service
        self.ingredient_service = ingredient_service
        super().__init__(title, parent)
        self._setup_ui()
        self._load_ingredients()
        self._load_data()

    # ===== UI 构建 =====

    def _setup_ui(self):
        # 顶部操作栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(ui.button_spacing)

        self.btn_add = QPushButton("新增出库")
        apply_css_class(self.btn_add, "primary")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self._do_stock_out)

        self.btn_batch = QPushButton("批量出库")
        apply_css_class(self.btn_batch, "success")
        self.btn_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_batch.clicked.connect(self._open_batch_dialog)

        self.btn_export = QPushButton("导出记录")
        apply_css_class(self.btn_export, "secondary")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.clicked.connect(self._export_records)

        top_bar.addWidget(self.btn_add)
        top_bar.addWidget(self.btn_batch)
        top_bar.addWidget(self.btn_export)
        top_bar.addStretch()
        self.content_layout.addLayout(top_bar)

        # 单条出库表单
        form_group = QGroupBox("新增出库")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 第一行：食材、数量
        row1 = QHBoxLayout()
        self.ingredient_combo = QComboBox()
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setPrefix("数量: ")

        row1.addWidget(QLabel("食材*:"))
        row1.addWidget(self.ingredient_combo, 1)
        row1.addWidget(self.quantity_spin)
        form_layout.addRow(row1)

        # 第二行：加权平均单价、用途、领用部门
        row2 = QHBoxLayout()
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        self.price_spin.setPrefix("¥ ")
        self.price_spin.setReadOnly(True)
        self.price_spin.setDecimals(2)

        self.purpose_edit = QLineEdit()
        self.purpose_edit.setPlaceholderText("用途")
        self.department_edit = QLineEdit()
        self.department_edit.setPlaceholderText("领用部门")

        row2.addWidget(QLabel("加权单价:"))
        row2.addWidget(self.price_spin)
        row2.addSpacing(10)
        row2.addWidget(QLabel("用途:"))
        row2.addWidget(self.purpose_edit, 1)
        row2.addWidget(QLabel("领用部门:"))
        row2.addWidget(self.department_edit, 1)
        form_layout.addRow(row2)

        # 第三行：操作人、备注
        row3 = QHBoxLayout()
        self.operator_edit = QLineEdit()
        self.operator_edit.setPlaceholderText("操作人")
        self.operator_edit.setText(Session.display_name)
        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("备注")

        row3.addWidget(QLabel("操作人:"))
        row3.addWidget(self.operator_edit, 1)
        row3.addWidget(QLabel("备注:"))
        row3.addWidget(self.remark_edit, 1)
        form_layout.addRow(row3)

        # 出库时间（仅特权角色可自定义，用于回溯录入历史出库）
        self.stock_out_time = None
        if Session.can_set_custom_time:
            row_time = QHBoxLayout()
            self.stock_out_time = QDateTimeEdit()
            self.stock_out_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            self.stock_out_time.setCalendarPopup(True)
            self.stock_out_time.setDateTime(QDateTime.currentDateTime())
            row_time.addWidget(QLabel("出库时间:"))
            row_time.addWidget(self.stock_out_time)
            row_time.addStretch()
            form_layout.addRow(row_time)

        self.content_layout.addWidget(form_group)

        # 筛选区
        filter_bar = QHBoxLayout()
        self.date_from = QDateTimeEdit()
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setCalendarPopup(True)
        self.date_from.setDateTime(QDateTime.currentDateTime().addDays(-30))

        self.date_to = QDateTimeEdit()
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setCalendarPopup(True)
        self.date_to.setDateTime(QDateTime.currentDateTime())

        self.btn_refresh = QPushButton("刷新")
        apply_css_class(self.btn_refresh, "secondary")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._load_data)

        filter_bar.addWidget(QLabel("日期范围:"))
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(QLabel("至"))
        filter_bar.addWidget(self.date_to)
        filter_bar.addStretch()
        filter_bar.addWidget(self.btn_refresh)
        self.content_layout.addLayout(filter_bar)

        # 出库记录表格
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "食材名称", "数量", "单价(加权平均)", "总价",
            "用途", "领用部门", "操作人", "备注", "时间", "操作",
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 120)
        self.table.setColumnWidth(9, 140)
        self.table.setColumnWidth(10, 80)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.content_layout.addWidget(self.table, 1)

        self.ingredient_combo.currentIndexChanged.connect(self._on_ingredient_changed)

    # ===== 数据加载 =====

    def _load_ingredients(self):
        self.ingredient_combo.clear()
        ingredients = self.ingredient_service.get_all_ingredients()
        for ing in ingredients:
            self.ingredient_combo.addItem(
                f"{ing.name} (当前库存: {ing.current_stock} {ing.unit})", ing.id
            )
        self._on_ingredient_changed()

    def _load_data(self):
        try:
            records = self.stock_service.get_stock_out_records()
            self._populate_table(records)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")

    def _populate_table(self, records):
        date_from = self.date_from.dateTime().toString("yyyy-MM-dd")
        date_to = self.date_to.dateTime().toString("yyyy-MM-dd")

        filtered = []
        for r in records:
            record_date = str(r.created_at)[:10]
            if date_from <= record_date <= date_to:
                filtered.append(r)

        self.table.setRowCount(len(filtered))
        for i, r in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.id)))
            self.table.setItem(i, 1, QTableWidgetItem(r.ingredient.name if r.ingredient else ""))
            self.table.setItem(i, 2, QTableWidgetItem(str(r.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(f"¥{r.unit_price:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"¥{r.total_price:.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(r.purpose or ""))
            self.table.setItem(i, 6, QTableWidgetItem(r.department or ""))
            self.table.setItem(i, 7, QTableWidgetItem(r.operator or ""))
            self.table.setItem(i, 8, QTableWidgetItem(r.remark or ""))
            self.table.setItem(i, 9, QTableWidgetItem(str(r.created_at)[:19]))

            btn_delete = QPushButton("删除")
            apply_css_class(btn_delete, "danger")
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.clicked.connect(
                lambda checked, rid=r.id: self._delete_record(rid)
            )
            self.table.setCellWidget(i, 10, btn_delete)

    # ===== 业务操作 =====

    def _on_ingredient_changed(self):
        ingredient_id = self.ingredient_combo.currentData()
        if not ingredient_id:
            return
        try:
            ingredient = self.stock_service.ingredient_repo.get_by_id(ingredient_id)
            if ingredient:
                self.quantity_spin.setMaximum(ingredient.current_stock)
            weighted_price = self.stock_service.get_weighted_price(ingredient_id)
            self.price_spin.setValue(weighted_price)
        except Exception:
            pass

    def _do_stock_out(self):
        ingredient_id = self.ingredient_combo.currentData()
        quantity = self.quantity_spin.value()

        if not ingredient_id or quantity <= 0:
            QMessageBox.warning(self, "警告", "请填写完整的出库信息")
            return

        try:
            created_at = (
                self.stock_out_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
                if self.stock_out_time else None
            )
            self.stock_service.stock_out(
                ingredient_id=ingredient_id,
                quantity=quantity,
                purpose=self.purpose_edit.text(),
                department=self.department_edit.text(),
                operator=self.operator_edit.text(),
                remark=self.remark_edit.text(),
                created_at=created_at,
            )
            QMessageBox.information(self, "提示", "出库成功")
            self._load_data()
            self._load_ingredients()
            self.quantity_spin.setValue(1)
            self.purpose_edit.clear()
            self.department_edit.clear()
            self.remark_edit.clear()
            self.data_changed.emit("stock_out")
        except InsufficientStockError as e:
            QMessageBox.warning(
                self, "库存不足",
                f"食材 [{e.ingredient}] 库存不足\n当前库存: {e.current}\n请求出库: {e.requested}",
            )
        except ExpiredIngredientError as e:
            QMessageBox.critical(
                self, "食品安全拦截",
                f"食材 [{e.ingredient}] 所有入库批次已过期，禁止出库",
            )
        except (ValidationError, NotFoundError, BusinessRuleError) as e:
            QMessageBox.critical(self, "错误", f"出库失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"出库操作异常: {e}")

    def _open_batch_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("批量出库")
        dialog.setMinimumWidth(800)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setSpacing(10)

        # 操作按钮行
        btn_row = QHBoxLayout()
        # 出库日期（仅特权角色可自定义，用于回溯录入历史出库）
        # 同时作为"加载入库数据"的查询日期
        batch_date = None
        if Session.can_set_custom_time:
            batch_date = QDateTimeEdit()
            batch_date.setDisplayFormat("yyyy-MM-dd")
            batch_date.setCalendarPopup(True)
            batch_date.setDateTime(QDateTime.currentDateTime())
            btn_row.addWidget(QLabel("出库日期:"))
            btn_row.addWidget(batch_date)
            btn_row.addSpacing(10)

        btn_load_today = QPushButton("加载入库数据")
        apply_css_class(btn_load_today, "success")
        btn_load_today.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_all = QPushButton("全选")
        apply_css_class(btn_select_all, "secondary")
        btn_deselect_all = QPushButton("取消全选")
        apply_css_class(btn_deselect_all, "secondary")
        btn_confirm = QPushButton("确认批量出库")
        apply_css_class(btn_confirm, "success")
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel = QPushButton("取消")
        apply_css_class(btn_cancel, "secondary")

        btn_row.addWidget(btn_load_today)
        btn_row.addWidget(btn_select_all)
        btn_row.addWidget(btn_deselect_all)
        btn_row.addStretch()
        btn_row.addWidget(btn_confirm)
        btn_row.addWidget(btn_cancel)
        dialog_layout.addLayout(btn_row)

        # 批量表格
        batch_table = QTableWidget()
        batch_table.setColumnCount(8)
        batch_table.setHorizontalHeaderLabels([
            "选择", "食材", "当前库存", "单位", "出库数量", "用途", "领用部门", "ID",
        ])
        batch_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        batch_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        batch_table.setColumnHidden(7, True)
        batch_table.setAlternatingRowColors(True)
        batch_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        dialog_layout.addWidget(batch_table)

        def load_stockin():
            try:
                # 特权角色可加载任意日期的入库数据；普通用户固定今天
                if batch_date is not None:
                    target_date = batch_date.dateTime().toString("yyyy-MM-dd")
                else:
                    target_date = datetime.now().strftime("%Y-%m-%d")
                StockIn = self.stock_service.stock_in_repo.model
                Ingredient = self.stock_service.ingredient_repo.model
                query = (
                    StockIn
                    .select(
                        StockIn.ingredient,
                        Ingredient.name,
                        Ingredient.current_stock,
                        Ingredient.unit,
                        fn.SUM(StockIn.quantity).alias("stockin_qty"),
                    )
                    .join(Ingredient, on=(StockIn.ingredient == Ingredient.id))
                    .where(fn.strftime("%Y-%m-%d", StockIn.created_at) == target_date)
                    .group_by(StockIn.ingredient)
                )
                rows = list(query.dicts())
                batch_table.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    chk = QTableWidgetItem()
                    chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    chk.setCheckState(Qt.CheckState.Checked)
                    batch_table.setItem(i, 0, chk)
                    batch_table.setItem(i, 1, QTableWidgetItem(row["name"] or ""))
                    batch_table.setItem(i, 2, QTableWidgetItem(str(row["current_stock"])))
                    batch_table.setItem(i, 3, QTableWidgetItem(row["unit"] or ""))
                    batch_table.setItem(i, 4, QTableWidgetItem(str(row["stockin_qty"] or 0)))
                    batch_table.setItem(i, 5, QTableWidgetItem("营养餐"))
                    batch_table.setItem(i, 6, QTableWidgetItem("食堂"))
                    id_item = QTableWidgetItem(str(row["ingredient"]))
                    id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    batch_table.setItem(i, 7, id_item)
                if batch_date is not None:
                    dialog.setWindowTitle(f"批量出库 - {target_date}")
            except Exception as e:
                QMessageBox.warning(dialog, "加载失败", f"加载入库数据失败: {e}")

        def select_all():
            for i in range(batch_table.rowCount()):
                item = batch_table.item(i, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Checked)

        def deselect_all():
            for i in range(batch_table.rowCount()):
                item = batch_table.item(i, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Unchecked)

        def confirm_batch():
            items = []
            for i in range(batch_table.rowCount()):
                chk = batch_table.item(i, 0)
                if not chk or chk.checkState() != Qt.CheckState.Checked:
                    continue
                id_item = batch_table.item(i, 7)
                qty_item = batch_table.item(i, 4)
                if not id_item or not qty_item:
                    continue
                try:
                    quantity = float(qty_item.text())
                except ValueError:
                    continue
                if quantity <= 0:
                    continue
                name_item = batch_table.item(i, 1)
                # 特权角色可指定出库日期（回溯录入）；普通用户由服务层忽略，使用当前时间
                created_at = None
                if batch_date is not None:
                    created_at = batch_date.dateTime().toString("yyyy-MM-dd HH:mm:ss")
                items.append({
                    "ingredient_id": int(id_item.text()),
                    "ingredient_name": name_item.text() if name_item else "",
                    "quantity": quantity,
                    "purpose": batch_table.item(i, 5).text() if batch_table.item(i, 5) else "",
                    "department": batch_table.item(i, 6).text() if batch_table.item(i, 6) else "",
                    "operator": self.operator_edit.text(),
                    "remark": "批量出库",
                    "created_at": created_at,
                })

            if not items:
                QMessageBox.warning(dialog, "警告", "没有选中的可出库数据")
                return

            result = self.stock_service.batch_stock_out(items)
            errors = result.data.get("errors", []) if result.data else []
            msg = result.message
            if errors:
                msg += "\n\n错误详情:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    msg += f"\n... 还有 {len(errors) - 5} 条错误"

            if result.success:
                QMessageBox.information(dialog, "提示", msg)
            else:
                QMessageBox.warning(dialog, "提示", msg)
            self._load_data()
            self._load_ingredients()
            self.data_changed.emit("stock_out")
            dialog.accept()

        btn_load_today.clicked.connect(load_stockin)
        btn_select_all.clicked.connect(select_all)
        btn_deselect_all.clicked.connect(deselect_all)
        btn_confirm.clicked.connect(confirm_batch)
        btn_cancel.clicked.connect(dialog.reject)

        load_stockin()
        dialog.exec()

    def _export_records(self):
        try:
            from ...services.utility_services import ExcelExportService
            exporter = ExcelExportService(stock_service=self.stock_service)
            success = exporter.export_stock_out_records(self)
            if success:
                QMessageBox.information(self, "提示", "导出成功")
            else:
                QMessageBox.warning(self, "警告", "导出失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出异常: {e}")

    def _delete_record(self, record_id):
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除该出库记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.stock_service.delete_stock_out(record_id)
            QMessageBox.information(self, "提示", "删除成功")
            self._load_data()
            self.data_changed.emit("stock_out")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    # ===== 页面回调 =====

    def refresh(self):
        self._load_data()
        self._load_ingredients()

    def on_show(self):
        self._load_data()
        self._load_ingredients()
