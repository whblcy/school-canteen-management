"""
Excel 导入导出处理模块 - macOS 风格
"""
import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from database import (CategoryDAO, SupplierDAO, IngredientDAO,
                      StockInDAO, StockOutDAO)


# macOS 风格配色
MAC_BLUE = "0071e3"
MAC_GREEN = "34c759"
MAC_RED = "ff3b30"
MAC_ORANGE = "ff9500"
MAC_GRAY = "86868b"
MAC_LIGHT_GRAY = "f5f5f7"
MAC_BORDER = "d2d2d7"


class ExcelHandler:
    """Excel 处理类"""

    @staticmethod
    def _create_header_style():
        """创建 macOS 风格表头样式"""
        return {
            'fill': PatternFill(start_color=MAC_LIGHT_GRAY, end_color=MAC_LIGHT_GRAY, fill_type="solid"),
            'font': Font(color="1d1d1f", bold=True, size=12, name="-apple-system"),
            'alignment': Alignment(horizontal="left", vertical="center"),
            'border': Border(
                bottom=Side(style='thin', color=MAC_BORDER)
            )
        }

    @staticmethod
    def _create_cell_style():
        """创建 macOS 风格单元格样式"""
        return {
            'font': Font(color="1d1d1f", size=11, name="-apple-system"),
            'alignment': Alignment(horizontal="left", vertical="center"),
            'border': Border(
                bottom=Side(style='thin', color='f0f0f0')
            )
        }

    @staticmethod
    def export_ingredients(parent_widget, file_path=None):
        """导出食材余量信息到 Excel"""
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "导出食材余量信息",
                f"食材余量_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel Files (*.xlsx)"
            )

        if not file_path:
            return False

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "食材余量"

            header_style = ExcelHandler._create_header_style()
            cell_style = ExcelHandler._create_cell_style()

            # 写入表头
            headers = ["ID", "食材名称", "分类", "规格", "单位", "当前库存", "安全库存", "库存状态", "供应商"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.fill = header_style['fill']
                cell.font = header_style['font']
                cell.alignment = header_style['alignment']
                cell.border = header_style['border']

            # 获取数据
            ingredients = IngredientDAO.get_all()

            # 写入数据
            for row, ing in enumerate(ingredients, 2):
                status = "正常" if ing.current_stock > ing.safety_stock else "库存不足"

                data = [
                    ing.id, ing.name, ing.category_name, ing.specification,
                    ing.unit, ing.current_stock, ing.safety_stock, status, ing.supplier_name
                ]

                for col, value in enumerate(data, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.font = cell_style['font']
                    cell.alignment = cell_style['alignment']
                    cell.border = cell_style['border']

                # 库存不足高亮
                if ing.current_stock <= ing.safety_stock:
                    for col in range(1, 10):
                        ws.cell(row=row, column=col).fill = PatternFill(
                            start_color="fff5f5", end_color="fff5f5", fill_type="solid"
                        )
                        ws.cell(row=row, column=col).font = Font(
                            color=MAC_RED, size=11, name="-apple-system"
                        )

            # 调整列宽
            column_widths = [8, 22, 14, 16, 10, 14, 14, 14, 18]
            for i, width in enumerate(column_widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = width

            # 添加汇总信息
            summary_row = len(ingredients) + 3
            ws.cell(row=summary_row, column=1, value="汇总信息")
            ws.cell(row=summary_row, column=1).font = Font(
                bold=True, size=13, color=MAC_BLUE, name="-apple-system"
            )

            ws.cell(row=summary_row + 1, column=1, value="食材种类总数:")
            ws.cell(row=summary_row + 1, column=2, value=len(ingredients))

            low_stock_count = sum(1 for ing in ingredients if ing.current_stock <= ing.safety_stock)
            ws.cell(row=summary_row + 2, column=1, value="库存预警数量:")
            ws.cell(row=summary_row + 2, column=2, value=low_stock_count)
            ws.cell(row=summary_row + 2, column=2).font = Font(
                color=MAC_RED, bold=True, name="-apple-system"
            )

            wb.save(file_path)
            return True

        except Exception as e:
            QMessageBox.critical(parent_widget, "导出失败", f"导出时发生错误:\n{str(e)}")
            return False

    @staticmethod
    def import_ingredients(parent_widget, file_path=None):
        """从 Excel 导入食材信息"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget,
                "导入食材信息",
                "",
                "Excel Files (*.xlsx)"
            )

        if not file_path:
            return False, "未选择文件"

        try:
            wb = load_workbook(file_path)
            ws = wb.active

            # 验证表头
            expected_headers = ["食材名称", "分类", "规格", "单位", "安全库存", "供应商"]
            actual_headers = [cell.value for cell in ws[1]]

            # 查找必需列的索引
            header_map = {}
            for i, header in enumerate(actual_headers):
                if header in expected_headers:
                    header_map[header] = i

            if "食材名称" not in header_map or "单位" not in header_map:
                return False, "Excel 格式不正确，必须包含'食材名称'和'单位'列"

            # 获取分类和供应商映射
            categories = {cat.name: cat.id for cat in CategoryDAO.get_all()}
            suppliers = {s.name: s.id for s in SupplierDAO.get_all()}

            success_count = 0
            error_count = 0
            errors = []

            # 从第2行开始读取数据
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
                try:
                    name = row[header_map.get("食材名称", 0)]
                    if not name:
                        continue

                    category_name = row[header_map.get("分类", 1)] if "分类" in header_map else None
                    specification = row[header_map.get("规格", 2)] if "规格" in header_map else ""
                    unit = row[header_map.get("单位", 3)] if "单位" in header_map else ""

                    safety_stock = 0
                    if "安全库存" in header_map:
                        try:
                            safety_stock = float(row[header_map["安全库存"]])
                        except (ValueError, TypeError):
                            safety_stock = 0

                    supplier_name = row[header_map.get("供应商", 5)] if "供应商" in header_map else None

                    # 处理分类
                    category_id = None
                    if category_name:
                        if category_name not in categories:
                            # 自动创建分类
                            CategoryDAO.add(category_name, f"从Excel导入: {category_name}")
                            categories = {cat.name: cat.id for cat in CategoryDAO.get_all()}
                        category_id = categories.get(category_name)

                    # 处理供应商
                    supplier_id = None
                    if supplier_name:
                        if supplier_name not in suppliers:
                            SupplierDAO.add(supplier_name)
                            suppliers = {s.name: s.id for s in SupplierDAO.get_all()}
                        supplier_id = suppliers.get(supplier_name)

                    # 添加食材
                    IngredientDAO.add(
                        name=str(name),
                        category_id=category_id,
                        unit=str(unit) if unit else "个",
                        specification=str(specification) if specification else "",
                        safety_stock=safety_stock,
                        supplier_id=supplier_id
                    )
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"第{row_idx}行: {str(e)}")

            result_msg = f"导入完成!\n成功: {success_count} 条\n失败: {error_count} 条"
            if errors:
                result_msg += "\n\n部分错误:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    result_msg += f"\n... 还有 {len(errors) - 5} 条错误"

            return True, result_msg

        except Exception as e:
            return False, f"导入失败: {str(e)}"

    @staticmethod
    def create_template(parent_widget):
        """创建 macOS 风格导入模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "保存导入模板",
            "食材导入模板.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return False

        try:
            wb = Workbook()

            # === 主模板页 ===
            ws = wb.active
            ws.title = "食材导入模板"

            # 标题行
            ws.merge_cells('A1:F1')
            title_cell = ws['A1']
            title_cell.value = "学校食堂食材导入模板"
            title_cell.font = Font(size=18, bold=True, color=MAC_BLUE, name="-apple-system")
            title_cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[1].height = 36

            # 副标题
            ws.merge_cells('A2:F2')
            subtitle_cell = ws['A2']
            subtitle_cell.value = "请按照下方格式填写食材信息，带 * 号为必填项"
            subtitle_cell.font = Font(size=11, color=MAC_GRAY, name="-apple-system")
            subtitle_cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[2].height = 24

            # 表头 (第4行)
            headers = [
                ("食材名称*", "食材的完整名称，如：大白菜、五花肉"),
                ("分类", "所属分类，如：蔬菜类、肉类、粮油类"),
                ("规格", "规格描述，如：新鲜、精品、散装"),
                ("单位*", "计量单位，如：斤、个、袋、桶"),
                ("安全库存", "库存预警阈值，低于此值会提醒补货"),
                ("供应商", "供应商名称，不存在会自动创建")
            ]

            header_fill = PatternFill(start_color=MAC_LIGHT_GRAY, end_color=MAC_LIGHT_GRAY, fill_type="solid")
            header_font = Font(color="1d1d1f", bold=True, size=12, name="-apple-system")
            header_border = Border(bottom=Side(style='medium', color=MAC_BORDER))

            for col, (header, _) in enumerate(headers, 1):
                cell = ws.cell(row=4, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.border = header_border
                cell.alignment = Alignment(horizontal="left", vertical="center")

            ws.row_dimensions[4].height = 28

            # 示例数据
            examples = [
                ["大白菜", "蔬菜类", "新鲜", "斤", 50, "绿源蔬菜批发"],
                ["五花肉", "肉类", "精品", "斤", 30, "鸿运肉业"],
                ["鸡蛋", "蛋类", "散养土鸡蛋", "个", 200, "阳光养殖场"],
                ["东北大米", "粮油类", "五常稻花香", "袋", 20, "金穗粮油"],
                ["食用油", "粮油类", "非转基因压榨", "桶", 10, "金穗粮油"],
                ["西红柿", "蔬菜类", "有机", "斤", 40, "绿源蔬菜批发"],
                ["鸡胸肉", "肉类", "冷冻", "斤", 25, "鸿运肉业"],
                ["豆腐", "豆制品", "嫩豆腐", "块", 30, "豆香坊"],
            ]

            cell_font = Font(size=11, name="-apple-system")
            for row_idx, example in enumerate(examples, 5):
                for col_idx, value in enumerate(example, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=value)
                    cell.font = cell_font
                    cell.border = Border(bottom=Side(style='thin', color='f0f0f0'))
                ws.row_dimensions[row_idx].height = 24

            # 调整列宽
            column_widths = [18, 14, 18, 10, 14, 18]
            for i, width in enumerate(column_widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = width

            # === 填写说明页 ===
            ws2 = wb.create_sheet("填写说明")

            # 标题
            ws2.merge_cells('A1:C1')
            ws2['A1'] = "填写说明"
            ws2['A1'].font = Font(size=16, bold=True, color=MAC_BLUE, name="-apple-system")
            ws2['A1'].alignment = Alignment(horizontal="left", vertical="center")
            ws2.row_dimensions[1].height = 32

            # 表头说明表格
            ws2['A3'] = "字段名"
            ws2['B3'] = "说明"
            ws2['C3'] = "是否必填"
            for col in range(1, 4):
                cell = ws2.cell(row=3, column=col)
                cell.font = Font(bold=True, size=12, name="-apple-system")
                cell.fill = PatternFill(start_color=MAC_LIGHT_GRAY, end_color=MAC_LIGHT_GRAY, fill_type="solid")
                cell.border = Border(bottom=Side(style='medium', color=MAC_BORDER))

            field_details = [
                ("食材名称", "食材的完整名称，建议简洁明了", "是"),
                ("分类", "食材所属分类。常见分类：蔬菜类、肉类、水产类、豆制品、粮油类、调味品、蛋类、水果类。不存在的分类会自动创建", "否"),
                ("规格", "食材的规格描述，如产地、等级、包装方式等", "否"),
                ("单位", "计量单位，如：斤、公斤、个、袋、桶、箱等", "是"),
                ("安全库存", "库存预警阈值。当库存低于此值时系统会提醒补货。不填默认为0", "否"),
                ("供应商", "供应商名称。不存在的供应商会自动创建", "否"),
            ]

            for row_idx, (field, desc, required) in enumerate(field_details, 4):
                ws2.cell(row=row_idx, column=1, value=field).font = Font(
                    bold=True, size=11, name="-apple-system"
                )
                ws2.cell(row=row_idx, column=2, value=desc).font = Font(
                    size=11, name="-apple-system"
                )
                req_cell = ws2.cell(row=row_idx, column=3, value=required)
                req_cell.font = Font(
                    bold=True, size=11,
                    color=MAC_RED if required == "是" else MAC_GREEN,
                    name="-apple-system"
                )
                req_cell.alignment = Alignment(horizontal="center")
                ws2.row_dimensions[row_idx].height = 28

            # 注意事项
            notice_row = len(field_details) + 6
            ws2.merge_cells(f'A{notice_row}:C{notice_row}')
            ws2.cell(row=notice_row, column=1, value="注意事项").font = Font(
                size=14, bold=True, color=MAC_ORANGE, name="-apple-system"
            )

            notices = [
                "1. 第一行（第4行）为表头，请勿删除或修改",
                "2. 从第5行开始填写实际数据",
                "3. 分类和供应商如果不存在，导入时会自动创建",
                "4. 安全库存请填写数字，不填默认为0",
                "5. 建议先下载此模板，按格式填写后再导入",
                "6. 导入前请确保数据准确，避免重复导入",
            ]

            for i, notice in enumerate(notices, notice_row + 1):
                ws2.merge_cells(f'A{i}:C{i}')
                cell = ws2.cell(row=i, column=1, value=notice)
                cell.font = Font(size=11, name="-apple-system")
                ws2.row_dimensions[i].height = 24

            ws2.column_dimensions['A'].width = 16
            ws2.column_dimensions['B'].width = 55
            ws2.column_dimensions['C'].width = 12

            # === 分类参考页 ===
            ws3 = wb.create_sheet("分类参考")
            ws3['A1'] = "系统默认分类"
            ws3['A1'].font = Font(size=14, bold=True, color=MAC_BLUE, name="-apple-system")

            default_categories = [
                "蔬菜类", "肉类", "水产类", "豆制品",
                "粮油类", "调味品", "蛋类", "水果类"
            ]

            for i, cat in enumerate(default_categories, 3):
                ws3.cell(row=i, column=1, value=cat).font = Font(
                    size=11, name="-apple-system"
                )

            ws3.column_dimensions['A'].width = 16

            wb.save(file_path)
            return True

        except Exception as e:
            QMessageBox.critical(parent_widget, "创建模板失败", str(e))
            return False

    @staticmethod
    def export_stock_records(parent_widget, record_type="in"):
        """导出出入库记录"""
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            f"导出{'入库' if record_type == 'in' else '出库'}记录",
            f"{'入库' if record_type == 'in' else '出库'}记录_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return False

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "记录"

            header_style = ExcelHandler._create_header_style()
            cell_style = ExcelHandler._create_cell_style()

            if record_type == "in":
                headers = ["ID", "食材", "数量", "单价", "总价", "供应商", "批次号", "生产日期", "保质期", "操作人", "备注", "时间"]
                records = StockInDAO.get_all(1000)

                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=1, column=col, value=header)
                    cell.fill = header_style['fill']
                    cell.font = header_style['font']
                    cell.border = header_style['border']

                for row, r in enumerate(records, 2):
                    data = [r.id, r.ingredient_name, r.quantity, r.unit_price,
                           r.total_price, r.supplier_id, r.batch_number,
                           r.production_date, r.expiry_date, r.operator, r.remark, r.created_at]
                    for col, value in enumerate(data, 1):
                        cell = ws.cell(row=row, column=col, value=value)
                        cell.font = cell_style['font']
                        cell.border = cell_style['border']
            else:
                headers = ["ID", "食材", "数量", "单价", "总价", "用途", "领用部门", "操作人", "备注", "时间"]
                records = StockOutDAO.get_all(1000)

                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=1, column=col, value=header)
                    cell.fill = header_style['fill']
                    cell.font = header_style['font']
                    cell.border = header_style['border']

                for row, r in enumerate(records, 2):
                    data = [r.id, r.ingredient_name, r.quantity, r.unit_price,
                           r.total_price, r.purpose, r.department, r.operator, r.remark, r.created_at]
                    for col, value in enumerate(data, 1):
                        cell = ws.cell(row=row, column=col, value=value)
                        cell.font = cell_style['font']
                        cell.border = cell_style['border']

            wb.save(file_path)
            return True

        except Exception as e:
            QMessageBox.critical(parent_widget, "导出失败", str(e))
            return False
