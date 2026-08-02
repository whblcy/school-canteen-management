"""用真实销售订单 Excel 验证重复导入防护（两次导入同一份文件）"""
import os
import sys
import uuid

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["CANTEEN_DB_OVERRIDE"] = os.path.abspath(
    f"canteen_excel_dedup_{uuid.uuid4().hex[:8]}.db"
)

from PyQt6.QtWidgets import QApplication
from school_canteen.data.database import initialize_database
from school_canteen.data.models import seed_default_data
from school_canteen.app import build_services
from school_canteen.core.session import Session
from school_canteen.utils.excel_handler import ExcelImporter

app = QApplication(sys.argv)
Session.current_user = type(
    "FakeUser", (), {"id": 1, "username": "admin", "role": "admin"}
)()

initialize_database()
seed_default_data()
services = build_services()
stock = services["stock"]

FILE = "表格/6月22-26引出列表_销售订单_20260620143446（数据来源）.xlsx"

print("=== 第一次导入真实销售订单 ===")
ok, msg = ExcelImporter.import_sales_orders(None, stock, file_path=FILE)
print(f"  ok={ok}")
print(f"  {msg}")
assert ok, msg

records = stock.get_stock_in_records()
print(f"  入库记录数: {len(records)}")
stock_map = {r.ingredient.name: r.ingredient.current_stock for r in records}

print()
print("=== 第二次导入同一份文件（应全部重复跳过） ===")
ok2, msg2 = ExcelImporter.import_sales_orders(None, stock, file_path=FILE)
print(f"  ok={ok2}")
print(f"  {msg2}")
assert ok2, msg2
assert "重复跳过" in msg2, f"提示应包含重复跳过: {msg2}"

records2 = stock.get_stock_in_records()
print(f"  入库记录数: {len(records2)}（应与第一次相同）")
assert len(records2) == len(records), f"{len(records)} -> {len(records2)}"

# 库存不变
stock_map2 = {r.ingredient.name: r.ingredient.current_stock for r in records2}
for name in stock_map:
    assert stock_map[name] == stock_map2.get(name), f"{name}: {stock_map[name]} -> {stock_map2.get(name)}"
print("✅ 两次导入后库存完全一致，未重复累加")

print()
print("=== 真实 Excel 重复导入防护验证通过 ===")
