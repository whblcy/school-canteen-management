"""
进货查验页面 - 批量查验、可点击单元格、查验记录保存
"""
from datetime import datetime

from PyQt6.QtWidgets import (
    QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QMessageBox,
    QDateTimeEdit, QMenu, QInputDialog,
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor
from peewee import fn

from ..base_page import BasePage
from ..style_helper import apply_css_class
from ...config import get_config
from ...utils.excel_handler import ExcelImporter

cfg = get_config()
ui = cfg.ui

# 可点击单元格所在列
COL_RESULT = 8
COL_INSPECTOR = 9


class InspectionView(BasePage):
    """进货查验记录管理页面"""

    def __init__(self, inspection_service, inspector_service, stock_service,
                 title, parent=None):
        self.inspection_service = inspection_service
        self.inspector_service = inspector_service
        self.stock_service = stock_service
        super().__init__(title, parent)
        self._setup_ui()
        self._load_data()

    # ===== UI 构建 =====

    def _setup_ui(self):
        # 顶部操作栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(ui.button_spacing)

        self.btn_batch = QPushButton("批量查验")
        self.btn_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_batch.clicked.connect(self._batch_load)

        self.btn_save = QPushButton("保存查验")
        apply_css_class(self.btn_save, "success")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_records)

        self.btn_import = QPushButton("导入查验记录")
        apply_css_class(self.btn_import, "primary")
        self.btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import.clicked.connect(self._import_inspection)

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

        top_bar.addWidget(self.btn_batch)
        top_bar.addWidget(self.btn_save)
        top_bar.addWidget(self.btn_import)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("日期范围:"))
        top_bar.addWidget(self.date_from)
        top_bar.addWidget(QLabel("至"))
        top_bar.addWidget(self.date_to)
        top_bar.addWidget(self.btn_refresh)
        self.content_layout.addLayout(top_bar)

        # 提示信息
        tip = QLabel("提示: 点击「查验结果」和「查验人」单元格可下拉选择，勾选记录后点击「保存查验」批量保存。")
        tip.setStyleSheet(f"color: {ui.color_text_secondary}; font-size: 12px;")
        self.content_layout.addWidget(tip)

        # 查验表格
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "✅", "ID", "食材名称", "数量", "单位", "生产日期", "保质期",
            "供应商", "查验结果", "查验人", "操作", "ingredient_id", "stock_in_id",
        ])
        self.table.setColumnHidden(11, True)
        self.table.setColumnHidden(12, True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 100)
        self.table.setColumnWidth(9, 100)
        self.table.setColumnWidth(10, 70)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMouseTracking(True)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.itemEntered.connect(self._on_item_entered)
        self.content_layout.addWidget(self.table, 1)

    # ===== 数据加载 =====

    def _load_data(self):
        """使用 inspection_service.get_by_date_range() 加载查验记录"""
        try:
            date_from = self.date_from.dateTime().toString("yyyy-MM-dd")
            date_to = self.date_to.dateTime().toString("yyyy-MM-dd")
            records = self.inspection_service.get_by_date_range(date_from, date_to)
            self._populate_from_inspection_records(records)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")

    def _import_inspection(self):
        try:
            success, msg = ExcelImporter.import_inspection_records(
                self, self.stock_service, self.inspection_service)
            if success:
                QMessageBox.information(self, "提示", msg)
                self._load_data()
            else:
                QMessageBox.warning(self, "导入失败", msg)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入异常: {e}")

    def _batch_load(self):
        """加载日期范围内的入库数据，用于批量查验"""
        try:
            date_from = self.date_from.dateTime().toString("yyyy-MM-dd")
            date_to = self.date_to.dateTime().toString("yyyy-MM-dd")

            StockIn = self.stock_service.stock_in_repo.model
            Ingredient = self.stock_service.ingredient_repo.model
            suppliers = {
                s.id: s.name
                for s in self.stock_service.supplier_repo.get_all_ordered()
            }

            query = (
                StockIn
                .select(StockIn, Ingredient)
                .join(Ingredient, on=(StockIn.ingredient == Ingredient.id))
                .where(
                    (fn.strftime("%Y-%m-%d", StockIn.created_at) >= date_from)
                    & (fn.strftime("%Y-%m-%d", StockIn.created_at) <= date_to)
                )
                .order_by(StockIn.created_at.desc())
            )
            rows = list(query)

            self.table.setRowCount(len(rows))
            for i, si in enumerate(rows):
                existing = self.inspection_service.get_by_stock_in(si.id)
                is_inspected = existing is not None

                # 复选框：已查验默认不选，未查验默认选中
                check_item = QTableWidgetItem()
                check_item.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                )
                check_item.setCheckState(
                    Qt.CheckState.Unchecked if is_inspected else Qt.CheckState.Checked
                )
                self.table.setItem(i, 0, check_item)

                # ID
                self.table.setItem(i, 1, QTableWidgetItem(str(si.id)))

                # 食材名称（已查验用绿色标记）
                name_item = QTableWidgetItem(si.ingredient.name if si.ingredient else "")
                if is_inspected:
                    name_item.setForeground(QColor(ui.color_green))
                self.table.setItem(i, 2, name_item)

                # 数量
                self.table.setItem(i, 3, QTableWidgetItem(str(si.quantity)))

                # 单位
                unit = si.ingredient.unit if si.ingredient else ""
                self.table.setItem(i, 4, QTableWidgetItem(unit))

                # 生产日期
                self.table.setItem(i, 5, QTableWidgetItem(str(si.production_date or "")))

                # 保质期
                self.table.setItem(i, 6, QTableWidgetItem(str(si.expiry_date or "")))

                # 供应商
                sup_name = suppliers.get(si.supplier_id, "") if si.supplier_id else ""
                self.table.setItem(i, 7, QTableWidgetItem(sup_name))

                # 查验结果（可点击单元格）
                result_text = "合格"
                if is_inspected and existing.inspection_result:
                    result_text = str(existing.inspection_result).strip()
                self._set_clickable_cell(i, COL_RESULT, result_text)

                # 查验人（可点击单元格）
                inspector_text = "--"
                if is_inspected and existing.inspector:
                    inspector_text = str(existing.inspector).strip()
                self._set_clickable_cell(i, COL_INSPECTOR, inspector_text)

                # 操作（删除按钮）
                btn_delete = QPushButton("删除")
                apply_css_class(btn_delete, "danger")
                btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_delete.clicked.connect(
                    lambda checked, row=i: self._delete_row(row)
                )
                self.table.setCellWidget(i, 10, btn_delete)

                # 隐藏列
                ing_id_item = QTableWidgetItem(str(si.ingredient_id))
                ing_id_item.setFlags(ing_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, 11, ing_id_item)

                si_id_item = QTableWidgetItem(str(si.id))
                si_id_item.setFlags(si_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, 12, si_id_item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载入库数据失败: {e}")

    def _populate_from_inspection_records(self, records):
        """从查验记录填充表格"""
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            is_inspected = bool(r.inspector and r.inspector.strip())

            # 复选框
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            check_item.setCheckState(
                Qt.CheckState.Unchecked if is_inspected else Qt.CheckState.Checked
            )
            self.table.setItem(i, 0, check_item)

            # ID
            self.table.setItem(i, 1, QTableWidgetItem(str(r.id)))

            # 食材名称
            name_item = QTableWidgetItem(r.ingredient.name if r.ingredient else "")
            if is_inspected:
                name_item.setForeground(QColor(ui.color_green))
            self.table.setItem(i, 2, name_item)

            # 数量
            self.table.setItem(i, 3, QTableWidgetItem(str(r.quantity)))

            # 单位
            self.table.setItem(i, 4, QTableWidgetItem(r.unit or ""))

            # 生产日期
            self.table.setItem(i, 5, QTableWidgetItem(str(r.production_date or "")))

            # 保质期
            self.table.setItem(i, 6, QTableWidgetItem(r.shelf_life or ""))

            # 供应商
            self.table.setItem(i, 7, QTableWidgetItem(r.supplier_name or ""))

            # 查验结果（可点击单元格）
            result_text = str(r.inspection_result or "合格").strip()
            self._set_clickable_cell(i, COL_RESULT, result_text)

            # 查验人（可点击单元格）
            inspector_text = str(r.inspector or "--").strip() or "--"
            self._set_clickable_cell(i, COL_INSPECTOR, inspector_text)

            # 操作（删除按钮）
            btn_delete = QPushButton("删除")
            apply_css_class(btn_delete, "danger")
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.clicked.connect(
                lambda checked, row=i: self._delete_row(row)
            )
            self.table.setCellWidget(i, 10, btn_delete)

            # 隐藏列
            ing_id_item = QTableWidgetItem(str(r.ingredient_id) if r.ingredient_id else "")
            ing_id_item.setFlags(ing_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 11, ing_id_item)

            si_id_item = QTableWidgetItem(str(r.stock_in_id) if r.stock_in_id else "")
            si_id_item.setFlags(si_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 12, si_id_item)

    # ===== 可点击单元格 =====

    def _set_clickable_cell(self, row, col, text):
        """设置可点击单元格样式：蓝色字体、下拉箭头、居中"""
        item = QTableWidgetItem(f"{text} ▼")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setForeground(QColor(ui.color_blue))
        self.table.setItem(row, col, item)

    def _on_cell_clicked(self, row, col):
        """点击可点击单元格时显示下拉菜单"""
        if col == COL_RESULT:
            menu = QMenu(self.table)
            for option in ["合格", "不合格"]:
                action = menu.addAction(option)
                action.triggered.connect(
                    lambda checked, r=row, c=col, t=option: self._set_cell_value(r, c, t)
                )
            cell_item = self.table.item(row, col)
            if cell_item:
                rect = self.table.visualItemRect(cell_item)
                menu.exec(self.table.mapToGlobal(rect.bottomLeft()))
        elif col == COL_INSPECTOR:
            menu = QMenu(self.table)
            names = self.inspector_service.get_names()
            for name in names:
                action = menu.addAction(name)
                action.triggered.connect(
                    lambda checked, r=row, c=col, t=name: self._set_cell_value(r, c, t)
                )
            menu.addSeparator()
            custom_action = menu.addAction("自定义...")
            custom_action.triggered.connect(
                lambda checked, r=row, c=col: self._set_custom_cell_value(r, c)
            )
            cell_item = self.table.item(row, col)
            if cell_item:
                rect = self.table.visualItemRect(cell_item)
                menu.exec(self.table.mapToGlobal(rect.bottomLeft()))

    def _on_item_entered(self, item):
        """鼠标悬停在可点击单元格上时变为手型光标"""
        col = self.table.column(item)
        if col == COL_RESULT or col == COL_INSPECTOR:
            self.table.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.table.setCursor(Qt.CursorShape.ArrowCursor)

    def _set_cell_value(self, row, col, text):
        """设置单元格值并保持可点击样式"""
        item = self.table.item(row, col)
        if item:
            item.setText(f"{text} ▼")
            item.setForeground(QColor(ui.color_blue))

    def _set_custom_cell_value(self, row, col):
        """自定义输入查验人"""
        text, ok = QInputDialog.getText(self, "自定义输入", "请输入查验人姓名：")
        if ok and text.strip():
            self._set_cell_value(row, col, text.strip())

    # ===== 业务操作 =====

    def _save_records(self):
        """批量保存查验记录"""
        records = []
        for i in range(self.table.rowCount()):
            check_item = self.table.item(i, 0)
            if not check_item or check_item.checkState() != Qt.CheckState.Checked:
                continue

            # 获取隐藏列数据
            ing_id_item = self.table.item(i, 11)
            si_id_item = self.table.item(i, 12)
            if not ing_id_item or not ing_id_item.text():
                continue

            try:
                ingredient_id = int(ing_id_item.text())
            except ValueError:
                continue

            stock_in_id = None
            if si_id_item and si_id_item.text():
                try:
                    stock_in_id = int(si_id_item.text())
                except ValueError:
                    stock_in_id = None

            # 获取查验结果
            result_item = self.table.item(i, COL_RESULT)
            inspection_result = ""
            if result_item:
                inspection_result = result_item.text().replace("▼", "").strip()

            # 获取查验人
            inspector_item = self.table.item(i, COL_INSPECTOR)
            inspector = ""
            if inspector_item:
                inspector = inspector_item.text().replace("▼", "").strip()

            if not inspector or inspector == "--":
                QMessageBox.warning(
                    self, "警告",
                    f"第 {i + 1} 行查验人为空，请填写后再保存",
                )
                return

            # 获取其他字段
            quantity_item = self.table.item(i, 3)
            try:
                quantity = float(quantity_item.text()) if quantity_item else 0
            except ValueError:
                quantity = 0

            unit_item = self.table.item(i, 4)
            unit = unit_item.text() if unit_item else ""

            prod_item = self.table.item(i, 5)
            production_date = prod_item.text() if prod_item else ""

            shelf_item = self.table.item(i, 6)
            shelf_life = shelf_item.text() if shelf_item else ""

            supplier_item = self.table.item(i, 7)
            supplier_name = supplier_item.text() if supplier_item else ""

            records.append({
                "stock_in": stock_in_id,
                "ingredient": ingredient_id,
                "quantity": quantity,
                "unit": unit,
                "production_date": production_date or None,
                "shelf_life": shelf_life,
                "supplier_name": supplier_name,
                "batch_number": "",
                "inspection_result": inspection_result,
                "inspector": inspector,
                "inspection_date": datetime.now().strftime("%Y-%m-%d"),
                "remark": "",
            })

        if not records:
            QMessageBox.warning(self, "警告", "没有选中的可保存数据")
            return

        try:
            insert_count, update_count = self.inspection_service.batch_save(records)
            QMessageBox.information(
                self, "保存成功",
                f"新增 {insert_count} 条，更新 {update_count} 条",
            )
            self._load_data()
            self.data_changed.emit("inspection")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def _delete_row(self, row):
        """删除表格行（如有查验记录则同时删除）"""
        si_id_item = self.table.item(row, 12)
        record_id_item = self.table.item(row, 1)

        reply = QMessageBox.question(
            self, "确认删除", "确定要删除该行吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 如果有 stock_in_id，尝试删除关联的查验记录
            if si_id_item and si_id_item.text():
                try:
                    stock_in_id = int(si_id_item.text())
                    existing = self.inspection_service.get_by_stock_in(stock_in_id)
                    if existing:
                        self.inspection_service.delete_record(existing.id)
                except Exception:
                    pass
            self.table.removeRow(row)
            QMessageBox.information(self, "提示", "删除成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    # ===== 页面回调 =====

    def refresh(self):
        self._load_data()

    def on_show(self):
        self._load_data()
