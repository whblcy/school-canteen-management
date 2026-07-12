"""学校食堂食材管理系统 - 全面自动化测试"""
import sys
import os
import traceback

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 删除旧数据库，从头测试
if os.path.exists('canteen.db'):
    os.remove('canteen.db')

results = []

def test(name, func):
    try:
        func()
        results.append(('PASS', name))
        print(f"  [PASS] {name}")
    except Exception as e:
        results.append(('FAIL', name, str(e)))
        print(f"  [FAIL] {name}: {e}")

print("=" * 60)
print("学校食堂食材管理系统 - 全面测试")
print("=" * 60)

def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)

# ========== 1. 数据库初始化 ==========
print("\n[1] 数据库初始化")
from database import (init_database, DB_PATH, get_connection, hash_password,
                      verify_password, UserDAO, CategoryDAO, SupplierDAO,
                      IngredientDAO, StockInDAO, StockOutDAO, InventoryCheckDAO,
                      ReportDAO, LogDAO)

test("数据库文件创建", lambda: (
    init_database(),
    assert_true(os.path.exists(DB_PATH), "数据库文件未创建")
))

def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)

# ========== 2. 用户认证 ==========
print("\n[2] 用户认证模块")

def test_default_admin():
    users = UserDAO.get_all()
    admin = [u for u in users if u.username == 'admin']
    assert_true(len(admin) > 0, "无管理员账号")

def test_correct_login():
    user = UserDAO.authenticate('admin', 'admin123')
    assert_true(user is not None, "正确密码登录失败")

def test_wrong_password():
    user = UserDAO.authenticate('admin', 'wrong')
    assert_true(user is None, "错误密码应被拒绝")

def test_nonexist_user():
    user = UserDAO.authenticate('nobody', 'test')
    assert_true(user is None, "不存在用户应返回None")

def test_add_user():
    ok = UserDAO.add('testuser', 'test123', '测试用户', 'user')
    assert_true(ok, "添加用户失败")

def test_duplicate_user():
    ok = UserDAO.add('testuser', 'test123')
    assert_true(not ok, "重复用户名应被拒绝")

def test_change_password():
    ok = UserDAO.update_password(1, 'newpassword123')
    assert_true(ok, "修改密码失败")
    user = UserDAO.authenticate('admin', 'newpassword123')
    assert_true(user is not None, "修改密码后验证失败")
    UserDAO.update_password(1, 'admin123')  # 恢复

def test_delete_user():
    users = UserDAO.get_all()
    test_u = [u for u in users if u.username == 'testuser']
    if test_u:
        ok = UserDAO.delete(test_u[0].id)
        assert_true(ok, "删除用户失败")
        users2 = UserDAO.get_all()
        assert_true(len([u for u in users2 if u.username == 'testuser']) == 0, "用户仍存在")

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

def test_default_categories():
    cats = CategoryDAO.get_all()
    assert_true(len(cats) >= 8, f"默认分类数量不足: {len(cats)}")

def test_add_category():
    ok = CategoryDAO.add('测试分类', '测试描述')
    assert_true(ok, "添加分类失败")

def test_duplicate_category():
    ok = CategoryDAO.add('测试分类')
    assert_true(not ok, "重复分类名应被拒绝")

def test_update_category():
    cats = CategoryDAO.get_all()
    tc = [c for c in cats if c.name == '测试分类']
    assert_true(len(tc) > 0, "测试分类不存在")
    ok = CategoryDAO.update(tc[0].id, '测试分类2', '新描述')
    assert_true(ok, "更新分类失败")
    cats2 = CategoryDAO.get_all()
    assert_true(any(c.name == '测试分类2' for c in cats2), "更新后分类名未变")

def test_delete_category():
    cats = CategoryDAO.get_all()
    tc = [c for c in cats if c.name == '测试分类2']
    if tc:
        ok = CategoryDAO.delete(tc[0].id)
        assert_true(ok, "删除分类失败")

test("获取默认分类列表", test_default_categories)
test("添加新分类", test_add_category)
test("重复分类名拒绝", test_duplicate_category)
test("更新分类", test_update_category)
test("删除分类", test_delete_category)

# ========== 4. 供应商管理 ==========
print("\n[4] 供应商管理模块")

def test_add_supplier():
    sid = SupplierDAO.add('测试供应商', '张三', '13800138000', '北京', 'test@test.com')
    assert_true(sid > 0, "添加供应商失败")

def test_get_suppliers():
    suppliers = SupplierDAO.get_all()
    assert_true(len(suppliers) > 0, "供应商列表为空")

def test_get_active_suppliers():
    suppliers = SupplierDAO.get_active()
    assert_true(len(suppliers) > 0, "活跃供应商列表为空")

def test_update_supplier():
    suppliers = SupplierDAO.get_all()
    s = [x for x in suppliers if x.name == '测试供应商']
    assert_true(len(s) > 0, "测试供应商不存在")
    ok = SupplierDAO.update(s[0].id, phone='13900139000')
    assert_true(ok, "更新供应商失败")
    s2 = SupplierDAO.get_all()
    assert_true(any(x.phone == '13900139000' for x in s2), "更新后电话未变")

def test_sql_injection_supplier():
    suppliers = SupplierDAO.get_all()
    s = [x for x in suppliers if x.name == '测试供应商']
    if s:
        SupplierDAO.update(s[0].id, **{"name'; DROP TABLE users; --": 'hack'})
        users = UserDAO.get_all()
        assert_true(len(users) > 0, "SQL注入防护失败! users表被删除")

def test_delete_supplier():
    suppliers = SupplierDAO.get_all()
    s = [x for x in suppliers if x.name == '测试供应商']
    if s:
        ok = SupplierDAO.delete(s[0].id)
        assert_true(ok, "删除供应商失败")

test("添加供应商", test_add_supplier)
test("获取供应商列表", test_get_suppliers)
test("获取活跃供应商", test_get_active_suppliers)
test("更新供应商", test_update_supplier)
test("SQL注入防护(供应商)", test_sql_injection_supplier)
test("删除供应商", test_delete_supplier)

# ========== 5. 食材管理 ==========
print("\n[5] 食材管理模块")

def test_add_ingredient():
    iid = IngredientDAO.add('测试白菜', 1, '斤', '新鲜', 50, None)
    assert_true(iid > 0, "添加食材失败")

def test_get_ingredients():
    ings = IngredientDAO.get_all()
    assert_true(len(ings) > 0, "食材列表为空")

def test_get_ingredient_by_id():
    ings = IngredientDAO.get_all()
    ing = [x for x in ings if x.name == '测试白菜']
    assert_true(len(ing) > 0, "测试白菜不存在")
    found = IngredientDAO.get_by_id(ing[0].id)
    assert_true(found is not None, "按ID获取食材失败")

def test_nonexist_id():
    found = IngredientDAO.get_by_id(99999)
    assert_true(found is None, "不存在的ID应返回None")

def test_update_stock():
    ings = IngredientDAO.get_all()
    ing = [x for x in ings if x.name == '测试白菜']
    assert_true(len(ing) > 0, "测试白菜不存在")
    old_stock = ing[0].current_stock
    ok = IngredientDAO.update_stock(ing[0].id, 10)
    assert_true(ok, "更新库存失败")
    updated = IngredientDAO.get_by_id(ing[0].id)
    assert_true(updated.current_stock == old_stock + 10, f"库存更新错误: {updated.current_stock} != {old_stock + 10}")

def test_sql_injection_ingredient():
    ings = IngredientDAO.get_all()
    ing = [x for x in ings if x.name == '测试白菜']
    if ing:
        IngredientDAO.update(ing[0].id, **{"name'; DROP TABLE users; --": 'hack'})
        users = UserDAO.get_all()
        assert_true(len(users) > 0, "SQL注入防护失败!")

def test_delete_ingredient():
    ings = IngredientDAO.get_all()
    ing = [x for x in ings if x.name == '测试白菜']
    if ing:
        ok = IngredientDAO.delete(ing[0].id)
        assert_true(ok, "删除食材失败")

test("添加食材", test_add_ingredient)
test("获取食材列表", test_get_ingredients)
test("按ID获取食材", test_get_ingredient_by_id)
test("不存在的ID返回None", test_nonexist_id)
test("更新食材库存", test_update_stock)
test("SQL注入防护(食材)", test_sql_injection_ingredient)
test("删除食材", test_delete_ingredient)

# ========== 6. 入库管理 ==========
print("\n[6] 入库管理模块")

# 创建测试食材
IngredientDAO.add('入库测试食材', 1, '斤', '新鲜', 50, None)

def test_stock_in():
    ings = IngredientDAO.get_all()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    StockInDAO.add(ting.id, 100, 5.0, operator='admin', remark='测试入库')
    updated = IngredientDAO.get_by_id(ting.id)
    assert_true(updated.current_stock == 100, f"入库后库存不正确: {updated.current_stock}")

def test_stock_in_records():
    records = StockInDAO.get_all()
    assert_true(len(records) > 0, "入库记录为空")

def test_stock_in_total_price():
    records = StockInDAO.get_all()
    r = [x for x in records if x.ingredient_name == '入库测试食材']
    assert_true(len(r) > 0, "入库测试食材记录不存在")
    assert_true(r[0].total_price == 500.0, f"入库总价错误: {r[0].total_price}")

def test_negative_quantity():
    ings = IngredientDAO.get_all()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    try:
        StockInDAO.add(ting.id, -10, 5.0)
        assert_true(False, "负数数量应被拒绝")
    except ValueError:
        pass  # 预期行为

test("入库操作", test_stock_in)
test("入库记录存在", test_stock_in_records)
test("入库总价计算正确", test_stock_in_total_price)
test("负数数量拒绝", test_negative_quantity)

# ========== 7. 出库管理 ==========
print("\n[7] 出库管理模块")

def test_stock_out():
    ings = IngredientDAO.get_all()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    old_stock = ting.current_stock
    ok, msg = StockOutDAO.add(ting.id, 30, 5.0, purpose='午餐', operator='admin')
    assert_true(ok, f"出库失败: {msg}")
    updated = IngredientDAO.get_by_id(ting.id)
    assert_true(updated.current_stock == old_stock - 30, f"出库后库存不正确: {updated.current_stock}")

def test_stock_out_records():
    records = StockOutDAO.get_all()
    assert_true(len(records) > 0, "出库记录为空")

def test_insufficient_stock():
    ings = IngredientDAO.get_all()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    ok, msg = StockOutDAO.add(ting.id, 99999, 5.0)
    assert_true(not ok, "库存不足应被拒绝")

test("正常出库", test_stock_out)
test("出库记录存在", test_stock_out_records)
test("库存不足拒绝", test_insufficient_stock)

# ========== 8. 库存盘点 ==========
print("\n[8] 库存盘点模块")

def test_inventory_check():
    ings = IngredientDAO.get_all()
    ting = [x for x in ings if x.name == '入库测试食材'][0]
    system_stock = ting.current_stock
    InventoryCheckDAO.add(ting.id, system_stock, 60, operator='admin', remark='盘点')
    updated = IngredientDAO.get_by_id(ting.id)
    assert_true(updated.current_stock == 60, f"盘点后库存未校正: {updated.current_stock}")

def test_inventory_records():
    records = InventoryCheckDAO.get_all()
    assert_true(len(records) > 0, "盘点记录为空")

def test_inventory_difference():
    records = InventoryCheckDAO.get_all()
    r = [x for x in records if x.ingredient_name == '入库测试食材']
    assert_true(len(r) > 0, "盘点记录不存在")
    expected_diff = 60 - r[0].system_stock
    assert_true(r[0].difference == expected_diff, f"差异计算错误: {r[0].difference} != {expected_diff}")

test("盘点操作", test_inventory_check)
test("盘点记录存在", test_inventory_records)
test("盘点差异计算正确", test_inventory_difference)

# ========== 9. 报表统计 ==========
print("\n[9] 报表统计模块")
from datetime import datetime
now = datetime.now()

def test_stock_summary():
    data = ReportDAO.get_stock_summary()
    assert_true(len(data) > 0, "库存汇总为空")

def test_monthly_in():
    data = ReportDAO.get_monthly_in(now.year, now.month)
    assert_true(isinstance(data, list), "月度入库统计失败")

def test_monthly_out():
    data = ReportDAO.get_monthly_out(now.year, now.month)
    assert_true(isinstance(data, list), "月度出库统计失败")

def test_inventory_value():
    val = ReportDAO.get_inventory_value()
    assert_true(isinstance(val, (int, float)), f"库存总值类型错误: {type(val)}")

def test_monthly_finance():
    data = ReportDAO.get_monthly_finance(now.year, now.month)
    assert_true('total_in' in data and 'total_out' in data, "月度财务统计字段缺失")

def test_yearly_finance():
    data = ReportDAO.get_yearly_finance(now.year)
    assert_true(len(data) == 12, f"年度趋势应有12条数据，实际{len(data)}条")

def test_expiry_warnings():
    data = ReportDAO.get_expiry_warnings(7)
    assert_true(isinstance(data, list), "过期预警查询失败")

def test_expired_items():
    data = ReportDAO.get_expired_items()
    assert_true(isinstance(data, list), "已过期食材查询失败")

test("库存汇总", test_stock_summary)
test("月度入库统计", test_monthly_in)
test("月度出库统计", test_monthly_out)
test("库存总值", test_inventory_value)
test("月度财务统计", test_monthly_finance)
test("年度财务趋势", test_yearly_finance)
test("过期预警", test_expiry_warnings)
test("已过期食材", test_expired_items)

# ========== 10. 操作日志 ==========
print("\n[10] 操作日志模块")

def test_add_log():
    LogDAO.add(1, "测试操作", "test", 1, "测试详情")

def test_get_logs():
    logs = LogDAO.get_all()
    assert_true(len(logs) > 0, "日志列表为空")

test("添加日志", test_add_log)
test("获取日志列表", test_get_logs)

# ========== 11. 低库存预警 ==========
print("\n[11] 低库存预警")

def test_low_stock():
    IngredientDAO.add('低库存测试', 1, '斤', '', 100, None)
    low = IngredientDAO.get_low_stock()
    assert_true(len(low) > 0, "低库存检测失败")

test("低库存食材检测", test_low_stock)

# ========== 12. PyQt6 UI 测试 ==========
print("\n[12] PyQt6 UI 测试")
from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)
app.setStyle('Fusion')

def test_login_dialog():
    from main import LoginDialog
    dlg = LoginDialog()
    assert_true(dlg.windowTitle() != "", "登录对话框标题为空")
    dlg.close()

def test_main_window():
    from main import MainWindow
    user = UserDAO.authenticate('admin', 'admin123')
    assert_true(user is not None, "无法获取测试用户")
    win = MainWindow(current_user=user)
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
