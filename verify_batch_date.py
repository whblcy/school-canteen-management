"""验证批量出库支持选择出库日期（管理员回溯录入，普通用户用当前时间）"""
import os
import sys
import uuid

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["CANTEEN_DB_OVERRIDE"] = os.path.abspath(
    f"canteen_batch_tmp_{uuid.uuid4().hex[:8]}.db"
)

from PyQt6.QtWidgets import QApplication
from school_canteen.data.database import initialize_database
from school_canteen.data.models import seed_default_data
from school_canteen.app import build_services
from school_canteen.core.session import Session

app = QApplication(sys.argv)
initialize_database()
seed_default_data()
services = build_services()
stock = services["stock"]
ing_svc = services["ingredient"]

# 准备食材与库存
ing = ing_svc.create_ingredient("批量日期食材", "肉类", "斤", "", 5, "供应商D")
stock.stock_in(ingredient_id=ing.id, quantity=100, unit_price=5.0, operator="admin")

passed = 0
def check(name, cond):
    global passed
    print(f"  {'✅' if cond else '❌'} {name}")
    assert cond, name
    passed += 1

print("=== 1. 管理员批量出库指定历史日期 ===")
Session.current_user = type("Admin", (), {"id": 1, "username": "admin", "role": "admin"})()
items = [{
    "ingredient_id": ing.id, "ingredient_name": "批量日期食材",
    "quantity": 10.0, "purpose": "营养餐", "department": "食堂",
    "operator": "admin", "remark": "批量出库",
    "created_at": "2026-06-10 14:30:00",
}]
result = stock.batch_stock_out(items)
check(f"批量出库成功: {result.success}", result.success)

records = stock.get_stock_out_records()
check(f"出库记录数: {len(records)}", len(records) == 1)
rec = records[0]
created = str(rec.created_at)
print(f"  created_at = {created!r}")
check("created_at 为指定的历史日期", created.startswith("2026-06-10 14:30"))
check("库存已扣减: 90", ing_svc.get_ingredient(ing.id).current_stock == 90.0)

print("=== 2. 普通用户批量出库（应使用当前时间） ===")
# 创建真实普通用户，避免 OperationLog 外键失败
user_svc = services["user"]
user_svc.create_user("normuser", "password123", role="user")
from school_canteen.data.models import User as UserModel
real_user = UserModel.get(UserModel.username == "normuser")
Session.current_user = real_user
items2 = [{
    "ingredient_id": ing.id, "ingredient_name": "批量日期食材",
    "quantity": 5.0, "purpose": "营养餐", "department": "食堂",
    "operator": "normuser", "remark": "批量出库",
    "created_at": "2026-01-01 08:00:00",  # 普通用户尝试伪造历史时间
}]
result2 = stock.batch_stock_out(items2)
check(f"批量出库成功: {result2.success}", result2.success)
if not result2.success:
    print(f"  errors: {result2.data.get('errors') if result2.data else ''}")
records2 = stock.get_stock_out_records()
rec2 = records2[0] if records2 else None
check("记录数=2", len(records2) == 2)
if rec2:
    created2 = str(rec2.created_at)
    print(f"  created_at = {created2!r}")
    check("普通用户忽略伪造时间（使用当前时间）", not created2.startswith("2026-01-01"))

print("=== 3. UI：管理员打开批量出库对话框显示日期选择器 ===")
from PyQt6.QtWidgets import QDateTimeEdit
from PyQt6.QtCore import Qt
from school_canteen.ui.views.stock_out_view import StockOutView
from school_canteen.ui.styles import MAIN_STYLE
app.setStyleSheet(MAIN_STYLE)

Session.current_user = type("Admin", (), {"id": 1, "username": "admin", "role": "admin"})()
view = StockOutView(stock, ing_svc, "出库管理")
# 检查 _open_batch_dialog 内部逻辑：通过源码检查日期框条件
import inspect
src = inspect.getsource(StockOutView._open_batch_dialog)
check("批量出库对话框含出库日期选择器代码", "batch_date = QDateTimeEdit()" in src)
check("confirm_batch 透传 created_at", '"created_at": created_at' in src)
check("加载入库数据支持任意日期", 'batch_date.dateTime().toString("yyyy-MM-dd")' in src)

print()
print(f"=== 全部 {passed} 项检查通过 ===")
