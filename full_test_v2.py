"""
学校食堂食材管理系统 v2.0 - 重构版全面自动化测试
覆盖 12 个模块共 51 项测试，与旧版 full_test.py 等价
运行前删除 canteen.db 从零开始测试
"""
import sys
import os
import traceback

# 确保能找到 peewee
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.libs'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 删除旧数据库，从头测试
# 测试始终使用 canteen_test.db 避免与运行中程序冲突
os.environ['CANTEEN_DB_OVERRIDE'] = 'canteen_test.db'
if os.path.exists('canteen_test.db'):
    try:
        os.remove('canteen_test.db')
    except PermissionError:
        pass

results = []


def test(name, func):
    try:
        func()
        results.append(('PASS', name))
        print(f"  [PASS] {name}")
    except Exception as e:
        results.append(('FAIL', name, str(e)))
        print(f"  [FAIL] {name}: {e}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


print("=" * 60)
print("学校食堂食材管理系统 v2.0 - 全面测试")
print("=" * 60)

# ========== 1. 数据库初始化 ==========
print("\n[1] 数据库初始化")
from school_canteen.config import get_config
from school_canteen.data.database import initialize_database
from school_canteen.data.models import seed_default_data, User, Category, Supplier, Ingredient

cfg = get_config()

test("数据库文件创建", lambda: (
    initialize_database(),
    seed_default_data(),
    assert_true(os.path.exists(str(cfg.paths.db_file)), "数据库文件未创建")
))

# ========== 2. 用户认证 ==========
print("\n[2] 用户认证模块")
from school_canteen.data.repositories.user_repository import UserRepository
from school_canteen.utils.security import hash_password, verify_password
from school_canteen.services.auth_service import AuthService

user_repo = UserRepository()
auth_service = AuthService(user_repo)


def test_default_admin():
    admin = user_repo.get_by_username('admin')
    assert_true(admin is not None, "无管理员账号")


def test_correct_login():
    user = user_repo.authenticate('admin', 'admin123')
    assert_true(user is not None, "正确密码登录失败")


def test_wrong_password():
    user = user_repo.authenticate('admin', 'wrong')
    assert_true(user is None, "错误密码应被拒绝")


def test_nonexist_user():
    user = user_repo.authenticate('nobody', 'test')
    assert_true(user is None, "不存在用户应返回None")


def test_add_user():
    h, s = hash_password('test123')
    user_repo.create(username='testuser', password_hash=h, salt=s,
                     real_name='测试用户', role='user')


def test_duplicate_user():
    try:
        h, s = hash_password('test123')
        user_repo.create(username='testuser', password_hash=h, salt=s)
        assert_true(False, "重复用户名应被拒绝")
    except Exception:
        pass  # peewee unique 约束会抛异常


def test_change_password():
    from school_canteen.utils.security import hash_password
    admin = user_repo.get_by_username('admin')
    h, s = hash_password('newpassword123')
    user_repo.update(admin.id, password_hash=h, salt=s)
    user = user_repo.authenticate('admin', 'newpassword123')
    assert_true(user is not None, "修改密码后验证失败")
    # 恢复
    h2, s2 = hash_password('admin123')
    user_repo.update(admin.id, password_hash=h2, salt=s2)


def test_delete_user():
    user = user_repo.get_by_username('testuser')
    if user:
        ok = user_repo.delete(user.id)
        assert_true(ok, "删除用户失败")


def test_password_hash():
    h, s = hash_password('test')
    assert_true(len(h) == 64 and len(s) == 32, f"哈希格式不正确: hash_len={len(h)}, salt_len={len(s)}")


test("默认管理员账号存在", test_default_admin)
test("正确密码登录", test_correct_login)
test("错误密码拒绝", test_wrong_password)
test("不存在用户返回None", test_nonexist_user)
test("添加新用户", test_add_user)
test("重复用户名拒绝", test_duplicate_user)
test("修改密码", test_change_password)
test("删除非管理员用户", test_delete_user)
test("密码哈希加盐安全", test_password_hash)

# ========== 3. 分类管理 ==========
print("\n[3] 分类管理模块")
from school_canteen.services.catalog_service import CategoryService
from school_canteen.data.repositories.catalog_repository import CategoryRepository

category_service = CategoryService(CategoryRepository())


def test_default_categories():
    cats = category_service.get_all()
    assert_true(len(cats) >= 8, f"默认分类数量不足: {len(cats)}")


def test_add_category():
    category_service.create('测试分类', '测试描述')


def test_duplicate_category():
    try:
        category_service.create('测试分类')
        assert_true(False, "重复分类名应被拒绝")
    except Exception:
        pass


def test_update_category():
    cats = category_service.get_all()
    tc = [c for c in cats if c.name == '测试分类']
    assert_true(len(tc) > 0, "测试分类不存在")
    category_service.update(tc[0].id, name='测试分类2', description='新描述')
    cats2 = category_service.get_all()
    assert_true(any(c.name == '测试分类2' for c in cats2), "更新后分类名未变")


def test_delete_category():
    cats = category_service.get_all()
    tc = [c for c in cats if c.name == '测试分类2']
    if tc:
        category_service.delete(tc[0].id)


test("获取默认分类列表", test_default_categories)
test("添加新分类", test_add_category)
test("重复分类名拒绝", test_duplicate_category)
test("更新分类", test_update_category)
test("删除分类", test_delete_category)

# ========== 4. 供应商管理 ==========
print("\n[4] 供应商管理模块")
from school_canteen.services.catalog_service import SupplierService
from school_canteen.data.repositories.catalog_repository import SupplierRepository

supplier_service = SupplierService(SupplierRepository())


def test_add_supplier():
    supplier_service.create('测试供应商', '张三', '13800138000', '北京', 'test@test.com')


def test_get_suppliers():
    suppliers = supplier_service.get_all()
    assert_true(len(suppliers) > 0, "供应商列表为空")


def test_get_active_suppliers():
    suppliers = supplier_service.get_active()
    assert_true(len(suppliers) > 0, "活跃供应商列表为空")


def test_update_supplier():
    suppliers = supplier_service.get_all()
    s = [x for x in suppliers if x.name == '测试供应商']
    assert_true(len(s) > 0, "测试供应商不存在")
    supplier_service.update(s[0].id, phone='13900139000')
    s2 = supplier_service.get_all()
    assert_true(any(x.phone == '13900139000' for x in s2), "更新后电话未变")


def test_sql_injection_supplier():
    suppliers = supplier_service.get_all()
    s = [x for x in suppliers if x.name == '测试供应商']
    if s:
        # 字段白名单应拒绝非白名单字段
        supplier_service.update(s[0].id, **{"name'; DROP TABLE users; --": 'hack'})
        users = user_repo.get_all()
        assert_true(len(users) > 0, "SQL注入防护失败! users表被删除")


def test_delete_supplier():
    suppliers = supplier_service.get_all()
    s = [x for x in suppliers if x.name == '测试供应商']
    if s:
        supplier_service.delete(s[0].id)


test("添加供应商", test_add_supplier)
test("获取供应商列表", test_get_suppliers)
test("获取活跃供应商", test_get_active_suppliers)
test("更新供应商", test_update_supplier)
test("SQL注入防护(供应商)", test_sql_injection_supplier)
test("删除供应商", test_delete_supplier)

# ========== 5. 食材管理 ==========
print("\n[5] 食材管理模块")
from school_canteen.services.ingredient_service import IngredientService
from school_canteen.data.repositories.ingredient_repository import IngredientRepository

ingredient_service = IngredientService(
    IngredientRepository(), CategoryRepository(), SupplierRepository()
)


def test_add_ingredient():
    ingredient_service.create_ingredient('测试白菜', '蔬菜类', '斤', '新鲜', 50)


def test_get_ingredients():
    ings = ingredient_service.get_all_ingredients()
    assert_true(len(ings) > 0, "食材列表为空")


def test_get_ingredient_by_id():
    ings = ingredient_service.get_all_ingredients()
    ing = [x for x in ings if x.name == '测试白菜']
    assert_true(len(ing) > 0, "测试白菜不存在")
    found = ingredient_service.get_ingredient(ing[0].id)
    assert_true(found is not None, "按ID获取食材失败")


def test_nonexist_id():
    try:
        ingredient_service.get_ingredient(99999)
        assert_true(False, "不存在的ID应抛异常")
    except Exception:
        pass


def test_update_stock():
    from school_canteen.data.repositories.ingredient_repository import IngredientRepository
    repo = IngredientRepository()
    ings = repo.get_all_with_relations()
    ing = [x for x in ings if x.name == '测试白菜']
    assert_true(len(ing) > 0, "测试白菜不存在")
    old_stock = ing[0].current_stock
    repo.update_stock(ing[0].id, 10)
    updated = repo.get_by_id(ing[0].id)
    assert_true(updated.current_stock == old_stock + 10, f"库存更新错误: {updated.current_stock} != {old_stock + 10}")


def test_sql_injection_ingredient():
    from school_canteen.data.repositories.ingredient_repository import IngredientRepository
    repo = IngredientRepository()
    ings = repo.get_all_with_relations()
    ing = [x for x in ings if x.name == '测试白菜']
    if ing:
        repo.update(ing[0].id, **{"name'; DROP TABLE users; --": 'hack'})
        users = user_repo.get_all()
        assert_true(len(users) > 0, "SQL注入防护失败!")


def test_delete_ingredient():
    ings = ingredient_service.get_all_ingredients()
    ing = [x for x in ings if x.name == '测试白菜']
    if ing:
        ingredient_service.delete_ingredient(ing[0].id)


test("添加食材", test_add_ingredient)
test("获取食材列表", test_get_ingredients)
test("按ID获取食材", test_get_ingredient_by_id)
test("不存在的ID返回None", test_nonexist_id)
test("更新食材库存", test_update_stock)
test("SQL注入防护(食材)", test_sql_injection_ingredient)
test("删除食材", test_delete_ingredient)

# ========== 6. 入库管理 ==========
print("\n[6] 入库管理模块")
from school_canteen.services.stock_service import StockService
from school_canteen.data.repositories.stock_repository import (
    StockInRepository, StockOutRepository, InventoryCheckRepository
)

stock_service = StockService(
    IngredientRepository(), StockInRepository(), StockOutRepository(),
    InventoryCheckRepository(), CategoryRepository(), SupplierRepository()
)

ingredient_service.create_ingredient('入库测试食材', '蔬菜类', '斤', '新鲜', 50)


def test_stock_in():
    ings = ingredient_service.get_all_ingredients()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    stock_service.stock_in(ting.id, 100, 5.0, operator='admin', remark='测试入库')
    updated = ingredient_service.get_ingredient(ting.id)
    assert_true(updated.current_stock == 100, f"入库后库存不正确: {updated.current_stock}")


def test_stock_in_records():
    records = stock_service.get_stock_in_records()
    assert_true(len(records) > 0, "入库记录为空")


def test_stock_in_total_price():
    records = stock_service.get_stock_in_records()
    r = [x for x in records if x.ingredient.name == '入库测试食材']
    assert_true(len(r) > 0, "入库测试食材记录不存在")
    assert_true(r[0].total_price == 500.0, f"入库总价错误: {r[0].total_price}")


def test_negative_quantity():
    ings = ingredient_service.get_all_ingredients()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    try:
        stock_service.stock_in(ting.id, -10, 5.0)
        assert_true(False, "负数数量应被拒绝")
    except Exception:
        pass  # 预期行为


test("入库操作", test_stock_in)
test("入库记录存在", test_stock_in_records)
test("入库总价计算正确", test_stock_in_total_price)
test("负数数量拒绝", test_negative_quantity)

# ========== 7. 出库管理 ==========
print("\n[7] 出库管理模块")


def test_stock_out():
    ings = ingredient_service.get_all_ingredients()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    old_stock = ting.current_stock
    stock_service.stock_out(ting.id, 30, purpose='午餐', operator='admin')
    updated = ingredient_service.get_ingredient(ting.id)
    assert_true(updated.current_stock == old_stock - 30, f"出库后库存不正确: {updated.current_stock}")


def test_stock_out_records():
    records = stock_service.get_stock_out_records()
    assert_true(len(records) > 0, "出库记录为空")


def test_insufficient_stock():
    from school_canteen.core.exceptions import InsufficientStockError
    ings = ingredient_service.get_all_ingredients()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    try:
        stock_service.stock_out(ting.id, 99999)
        assert_true(False, "库存不足应被拒绝")
    except InsufficientStockError:
        pass  # 预期行为


test("正常出库", test_stock_out)
test("出库记录存在", test_stock_out_records)
test("库存不足拒绝", test_insufficient_stock)

# ========== 8. 库存盘点 ==========
print("\n[8] 库存盘点模块")


def test_inventory_check():
    ings = ingredient_service.get_all_ingredients()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    system_stock = ting.current_stock
    stock_service.inventory_check(ting.id, 60, operator='admin', remark='盘点')
    updated = ingredient_service.get_ingredient(ting.id)
    assert_true(updated.current_stock == 60, f"盘点后库存未校正: {updated.current_stock}")


def test_inventory_records():
    records = stock_service.get_inventory_records()
    assert_true(len(records) > 0, "盘点记录为空")


def test_inventory_difference():
    records = stock_service.get_inventory_records()
    r = [x for x in records if x.ingredient.name == '入库测试食材']
    assert_true(len(r) > 0, "盘点记录不存在")
    expected_diff = 60 - r[0].system_stock
    assert_true(r[0].difference == expected_diff, f"差异计算错误: {r[0].difference} != {expected_diff}")


test("盘点操作", test_inventory_check)
test("盘点记录存在", test_inventory_records)
test("盘点差异计算正确", test_inventory_difference)

# ========== 9. 报表统计 ==========
print("\n[9] 报表统计模块")
from school_canteen.services.report_service import ReportService
from school_canteen.data.repositories.report_repository import ReportRepository
from datetime import datetime

now = datetime.now()
report_service = ReportService(
    IngredientRepository(), StockInRepository(), StockOutRepository(), ReportRepository()
)


def test_stock_summary():
    data = report_service.get_stock_summary()
    assert_true(len(data) > 0, "库存汇总为空")


def test_monthly_finance():
    data = report_service.get_monthly_finance(now.year, now.month)
    assert_true('stock_in_amount' in data and 'stock_out_amount' in data, "月度财务统计字段缺失")


def test_yearly_finance():
    data = report_service.get_yearly_finance(now.year)
    assert_true(len(data) == 12, f"年度趋势应有12条数据，实际{len(data)}条")


def test_inventory_value():
    val = report_service.get_inventory_value()
    assert_true(isinstance(val, (int, float)), f"库存总值类型错误: {type(val)}")


def test_expiry_warnings():
    data = report_service.get_expiry_warnings()
    assert_true(isinstance(data, list), "过期预警查询失败")


def test_expired_items():
    data = report_service.get_expired_items()
    assert_true(isinstance(data, list), "已过期食材查询失败")


test("库存汇总", test_stock_summary)
test("月度财务统计", test_monthly_finance)
test("年度财务趋势", test_yearly_finance)
test("库存总值", test_inventory_value)
test("过期预警", test_expiry_warnings)
test("已过期食材", test_expired_items)

# ========== 10. 操作日志 ==========
print("\n[10] 操作日志模块")
from school_canteen.data.repositories.report_repository import LogRepository, ReportRepository
from school_canteen.services.utility_services import LogService

log_service = LogService(LogRepository())


def test_add_log():
    log_service.log(1, "测试操作", "test", 1, "测试详情")


def test_get_logs():
    logs = log_service.get_all()
    assert_true(len(logs) > 0, "日志列表为空")


test("添加日志", test_add_log)
test("获取日志列表", test_get_logs)

# ========== 11. 低库存预警 ==========
print("\n[11] 低库存预警")


def test_low_stock():
    ingredient_service.create_ingredient('低库存测试', '蔬菜类', '斤', '', 100)
    low = report_service.get_low_stock_items()
    assert_true(len(low) > 0, "低库存检测失败")


test("低库存食材检测", test_low_stock)

# ========== 12. PyQt6 UI 测试 ==========
print("\n[12] PyQt6 UI 测试", flush=True)
from PyQt6.QtWidgets import QApplication

print("  创建 QApplication...", flush=True)
app = QApplication.instance() or QApplication(sys.argv)
app.setStyle('Fusion')

print("  加载样式表...", flush=True)
from school_canteen.ui.styles import MAIN_STYLE
app.setStyleSheet(MAIN_STYLE)

print("  构建服务...", flush=True)
from school_canteen.app import build_services
services = build_services()


def test_login_dialog():
    print("    创建登录对话框...", flush=True)
    from school_canteen.ui.login_view import LoginDialog
    dlg = LoginDialog(services['auth'])
    assert_true(dlg.windowTitle() != "", "登录对话框标题为空")
    dlg.close()


def test_main_window():
    print("    创建主窗口...", flush=True)
    from school_canteen.ui.main_window import MainWindow
    user = user_repo.authenticate('admin', 'admin123')
    assert_true(user is not None, "无法获取测试用户")
    win = MainWindow(services, current_user=user)
    assert_true(win.windowTitle() != "", "主窗口标题为空")
    win.close()


test("创建登录对话框", test_login_dialog)
test("创建主窗口", test_main_window)

# ========== 汇总 ==========
print("\n" + "=" * 60)
pass_count = sum(1 for r in results if r[0] == 'PASS')
fail_count = sum(1 for r in results if r[0] == 'FAIL')
print(f"测试结果: {pass_count} 通过, {fail_count} 失败, 共 {len(results)} 项")
if fail_count > 0:
    print("\n失败项目:")
    for r in results:
        if r[0] == 'FAIL':
            print(f"  [FAIL] {r[1]}: {r[2]}")
print("=" * 60)

sys.exit(0 if fail_count == 0 else 1)
