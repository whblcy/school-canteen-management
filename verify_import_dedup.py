"""验证销售订单重复导入防护：同一份数据导入两次，第二次应全部跳过且库存不累加"""
import os
import sys
import uuid

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["CANTEEN_DB_OVERRIDE"] = os.path.abspath(
    f"canteen_dedup_tmp_{uuid.uuid4().hex[:8]}.db"
)

from school_canteen.data.database import initialize_database
from school_canteen.data.models import seed_default_data
from school_canteen.app import build_services
from school_canteen.core.session import Session

# 以 admin 登录（特权角色）
Session.current_user = type(
    "FakeUser", (), {"id": 1, "username": "admin", "role": "admin"}
)()

initialize_database()
seed_default_data()
services = build_services()
stock = services["stock"]

# 模拟一份销售订单 Excel 解析后的汇总数据（同 import_sales_orders 的 summary_data）
samples = [
    dict(product_name="三黄鸡", quantity=450.8, unit_price=17.3, unit="斤",
         category_name="肉类", supplier_name="供应商A", batch_number="PO-2026-001",
         production_date="", expiry_date="", operator="张三",
         stockin_date="2026-06-22", stockin_created_at="2026-06-22 08:00:00"),
    dict(product_name="鸡蛋", quantity=246.0, unit_price=5.66, unit="斤",
         category_name="蛋类", supplier_name="供应商B", batch_number="PO-2026-001",
         production_date="", expiry_date="", operator="张三",
         stockin_date="2026-06-22", stockin_created_at="2026-06-22 08:00:00"),
    dict(product_name="西红柿", quantity=174.0, unit_price=3.3, unit="斤",
         category_name="蔬菜", supplier_name="供应商C", batch_number="PO-2026-002",
         production_date="", expiry_date="", operator="李四",
         stockin_date="2026-06-23", stockin_created_at="2026-06-23 08:00:00"),
]


def do_import(tag):
    """模拟一次完整导入，返回 (新增, 跳过)"""
    added = skipped = 0
    for item in samples:
        rec = stock.import_stock_in(
            product_name=item["product_name"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            unit=item["unit"],
            category_name=item["category_name"],
            supplier_name=item["supplier_name"],
            batch_number=item["batch_number"],
            production_date=item["production_date"],
            expiry_date=item["expiry_date"],
            operator=item["operator"],
            created_at=item["stockin_created_at"],
            remark="从销售订单导入",
        )
        if rec is None:
            skipped += 1
        else:
            added += 1
    print(f"[{tag}] 新增={added} 重复跳过={skipped}")
    return added, skipped


print("=== 第一次导入（应全部新增） ===")
a1, s1 = do_import("第1次")
assert a1 == 3 and s1 == 0, f"第一次导入应 3 新增，实际 {a1}/{s1}"

# 记录第一次导入后的库存
stock_after_first = {
    ing.name: ing.current_stock
    for ing in services["ingredient"].get_all_ingredients()
    if ing.name in ("三黄鸡", "鸡蛋", "西红柿")
}
print(f"第一次导入后库存: {stock_after_first}")
assert stock_after_first["三黄鸡"] == 450.8, stock_after_first

print()
print("=== 第二次导入同一份数据（应全部重复跳过） ===")
a2, s2 = do_import("第2次")
assert a2 == 0 and s2 == 3, f"第二次导入应 0 新增 3 跳过，实际 {a2}/{s2}"

stock_after_second = {
    ing.name: ing.current_stock
    for ing in services["ingredient"].get_all_ingredients()
    if ing.name in ("三黄鸡", "鸡蛋", "西红柿")
}
print(f"第二次导入后库存: {stock_after_second}")
assert stock_after_second == stock_after_first, "重复导入后库存不应变化"
print("✅ 重复导入未累加库存")

print()
print("=== 记录总数检查 ===")
records = stock.get_stock_in_records()
print(f"入库记录总数: {len(records)}（应为 3）")
assert len(records) == 3, len(records)

print()
print("=== 合法变更新数据（应正常新增） ===")
# 不同日期、不同数量 → 不判重复
rec = stock.import_stock_in(
    product_name="三黄鸡", quantity=100.0, unit_price=17.3, unit="斤",
    category_name="肉类", supplier_name="供应商A", batch_number="PO-2026-003",
    operator="张三", created_at="2026-06-25 08:00:00", remark="从销售订单导入",
)
assert rec is not None, "合法变更新数据不应被判重复"
print("✅ 不同日期/数量/单据号 → 正常新增")

print()
print("=== 全量去重验证通过 ===")
