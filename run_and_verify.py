# -*- coding: utf-8 -*-
"""
启动 V2 桌面应用并做全功能验证（无显示器环境下用 offscreen 平台）。
不污染真实数据库：通过 CANTEEN_DB_OVERRIDE 指向临时库。
"""
import os
import sys
import shutil
import glob
import uuid

# ===== 必须在 import school_canteen 之前设置 =====
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["CANTEEN_DB_OVERRIDE"] = "canteen_verify_tmp.db"

# stub 掉 QMessageBox：offscreen 下静态弹窗会进入阻塞事件循环无人关闭
import PyQt6.QtWidgets as qtw


class StubMessageBox(qtw.QMessageBox):
    @staticmethod
    def information(*a, **k):
        return qtw.QMessageBox.StandardButton.Ok

    @staticmethod
    def warning(*a, **k):
        return qtw.QMessageBox.StandardButton.Ok

    @staticmethod
    def critical(*a, **k):
        msg = k.get("text") if "text" in k else (a[2] if len(a) > 2 else "")
        print(f"  [QMessageBox.critical] {msg}")
        return qtw.QMessageBox.StandardButton.Ok

    @staticmethod
    def question(*a, **k):
        return qtw.QMessageBox.StandardButton.Yes


qtw.QMessageBox = StubMessageBox

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDateTime, QTimer

from school_canteen.data.database import initialize_database
from school_canteen.data.models import seed_default_data
from school_canteen.app import build_services
from school_canteen.core.session import Session
from school_canteen.ui.login_view import LoginDialog
from school_canteen.ui.main_window import MainWindow

ROOT = os.path.dirname(os.path.abspath(__file__))
SHOT_DIR = os.path.join(ROOT, "verify_screenshots")
OUT_DIR = os.path.join(ROOT, "verify_reports")
os.makedirs(SHOT_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

results = {"pass": [], "fail": []}


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" -- {detail}" if detail and not ok else ""))
    results["pass" if ok else "fail"].append(name)


def main():
    # ---------- 0. 清理历史临时库，保证从干净状态启动 ----------
    for f in glob.glob(os.path.join(ROOT, "canteen_verify_tmp.db*")):
        try:
            os.remove(f)
        except Exception:
            pass

    # ---------- 1. 初始化 ----------
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    initialize_database()
    seed_default_data()

    from school_canteen.data.repositories.user_repository import UserRepository
    admin = UserRepository().get_by_username("admin")
    check("数据库初始化 + 默认数据(seed)", admin is not None,
          "admin 用户缺失" if admin is None else "")

    services = build_services()
    check("服务层 DI 装配(build_services)", services is not None and "stock" in services)

    # ---------- 2. 真实登录流程 ----------
    dlg = LoginDialog(services["auth"])
    dlg.username_input.setText("admin")
    dlg.password_input.setText("admin123")
    dlg._on_login()
    check("登录对话框(真实表单)登录成功",
          dlg.current_user is not None and dlg.current_user.username == "admin",
          "默认凭证 admin/admin123 登录失败" if dlg.current_user is None else "")
    Session.current_user = dlg.current_user  # 模拟全局会话

    # 错误密码应被拒
    from school_canteen.core.exceptions import AuthorizationError
    bad = False
    try:
        services["auth"].login("admin", "wrong")
    except Exception:
        bad = True
    check("错误密码被拒绝", bad)

    # ---------- 3. 构建主窗口 + 遍历所有页签 ----------
    window = MainWindow(services, dlg.current_user)
    window.resize(1280, 800)
    window.show()
    app.processEvents()

    nav = window.nav_list
    nav_count = nav.count()
    check("主窗口构建 + 导航项加载", nav_count >= 13, f"导航项数={nav_count}")

    page_build_ok = 0
    page_refresh_ok = 0
    for i in range(nav_count):
        item = nav.item(i)
        page_id = item.data(0x100)  # Qt.ItemDataRole.UserRole
        try:
            nav.setCurrentRow(i)
            app.processEvents()
            page = window.pages.get(page_id)
            if page is None:
                raise RuntimeError("页面未创建")
            page_build_ok += 1
            # 触发刷新
            try:
                page.refresh()
                app.processEvents()
                page_refresh_ok += 1
            except Exception as e:
                print(f"    [refresh 异常] {page_id}: {e}")
        except Exception as e:
            print(f"    [页面异常] {page_id}: {e}")
    check("全部页签构建无异常", page_build_ok == nav_count,
          f"成功 {page_build_ok}/{nav_count}")
    check("全部页签刷新无异常", page_refresh_ok == nav_count,
          f"成功 {page_refresh_ok}/{nav_count}")

    # ---------- 4. 业务流 + UI 数据反映 ----------
    # 创建食材(自动建分类/供应商)
    ing = services["ingredient"].create_ingredient(
        name="验证测试米_" + uuid.uuid4().hex[:6], category_name="粮油类",
        supplier_name="验证供应商",
        unit="kg", specification="", safety_stock=10)
    check("食材创建(自动建分类/供应商)", ing is not None and ing.id is not None)

    # 入库(管理员自定义历史时间)
    rec_in = services["stock"].stock_in(
        ingredient_id=ing.id, quantity=100, unit_price=5.0,
        supplier_id=ing.supplier_id, created_at="2026-06-10 08:00:00")
    check("入库成功 + 库存更新", rec_in is not None and
          services["ingredient"].get_ingredient(ing.id).current_stock == 100,
          f"库存={services['ingredient'].get_ingredient(ing.id).current_stock}")

    # 出库
    rec_out = services["stock"].stock_out(
        ingredient_id=ing.id, quantity=30, operator="测试员")
    check("出库成功 + 库存回冲", rec_out is not None and
          services["ingredient"].get_ingredient(ing.id).current_stock == 70,
          f"库存={services['ingredient'].get_ingredient(ing.id).current_stock}")

    # 删除入库回冲
    services["stock"].delete_stock_in(rec_in.id)
    check("删除入库回冲库存",
          services["ingredient"].get_ingredient(ing.id).current_stock == -30,
          f"库存={services['ingredient'].get_ingredient(ing.id).current_stock}")
    # 还原，便于后续报表验证（重新入库）
    services["stock"].stock_in(
        ingredient_id=ing.id, quantity=100, unit_price=5.0,
        supplier_id=ing.supplier_id, created_at="2026-06-10 08:00:00")

    # UI 表格反映数据：加载 stock_in 页面并放宽日期范围
    sin_page = window.pages.get("stock_in")
    if sin_page is not None:
        sin_page.date_from.setDateTime(QDateTime(2026, 1, 1, 0, 0, 0))
        sin_page.date_to.setDateTime(QDateTime(2026, 12, 31, 23, 59, 59))
        sin_page._load_data()
        app.processEvents()
        n_rows = sin_page.table.rowCount()
        check("入库页表格正确反映记录", n_rows >= 1, f"表格行数={n_rows}")
    else:
        check("入库页表格正确反映记录", False, "stock_in 页不存在")

    # 进货查验记录写入
    sin_rec = services["stock"].get_stock_in_records()[0]
    ing_unit = services["ingredient"].get_ingredient(sin_rec.ingredient_id).unit
    insp = services["inspection"].upsert_record(
        stock_in_id=sin_rec.id,
        ingredient_id=sin_rec.ingredient_id,
        quantity=sin_rec.quantity,
        unit=ing_unit,
        inspector_name="张三", production_date="2026-06-01",
        expiry_date="2026-07-01", qualification=True,
        batch_number="B001", record_person="测试员")
    check("进货查验记录写入", insp is not None and insp.id is not None)

    # ---------- 5. 报表导出(走 UI 层 ReportExportService) ----------
    res = services["report_export"]
    daily = os.path.join(OUT_DIR, "daily.xlsx")
    monthly = os.path.join(OUT_DIR, "monthly.xlsx")
    fin = os.path.join(OUT_DIR, "financial.xlsx")
    insp_rpt = os.path.join(OUT_DIR, "inspection.xlsx")
    try:
        res.export_daily_stock_sheet(daily, 2026, 6, 10)
        res.export_monthly_summary(monthly, 2026, 6)
        res.export_financial_report(fin, 2026)
        res.export_inspection_report(insp_rpt, 2026, 6)
        sizes = [os.path.getsize(p) for p in (daily, monthly, fin, insp_rpt)]
        check("4 类报表导出生成非空文件", all(s > 0 for s in sizes),
              f"文件大小={sizes}")
    except Exception as e:
        check("4 类报表导出生成非空文件", False, str(e))

    # ---------- 6. 数据清理(设置页) ----------
    try:
        services["data_mgmt"].clear_data("all_data", "确认删除")
        remaining = len(services["stock"].get_stock_in_records())
        check("数据清理(all_data)成功清空", remaining == 0,
              f"剩余入库={remaining}")
    except Exception as e:
        check("数据清理(all_data)成功清空", False, str(e))

    # 恢复默认数据（清理会保留用户，但清空了库存；重新 seed 分类/查验人）
    try:
        seed_default_data()
    except Exception:
        pass

    # ---------- 7. 截图 ----------
    shot_ok = 0
    for pid in ["overview", "stock_in", "report_export", "ingredients"]:
        try:
            # 找到对应 nav 行
            for i in range(nav_count):
                if nav.item(i).data(0x100) == pid:
                    nav.setCurrentRow(i)
                    break
            app.processEvents()
            QTimer.singleShot(50, lambda: None)
            app.processEvents()
            pix = window.grab()
            path = os.path.join(SHOT_DIR, f"{pid}.png")
            if pix.save(path):
                shot_ok += 1
        except Exception as e:
            print(f"    [截图异常] {pid}: {e}")
    # 主窗口整体截图
    try:
        if window.grab().save(os.path.join(SHOT_DIR, "main.png")):
            shot_ok += 1
    except Exception as e:
        print(f"    [主窗口截图异常] {e}")
    check("关键页面截图生成", shot_ok >= 1, f"截图 {shot_ok} 张")

    # ---------- 8. 真正跑一次事件循环验证不阻塞 ----------
    try:
        QTimer.singleShot(200, app.quit)
        app.exec()
        check("主事件循环可正常起停", True)
    except Exception as e:
        check("主事件循环可正常起停", False, str(e))

    # ---------- 收尾 ----------
    app.closeAllWindows()
    summary = (f"\n==== 验证汇总 ====\n"
               f"通过: {len(results['pass'])}   失败: {len(results['fail'])}")
    if results["fail"]:
        summary += "\n失败项:\n - " + "\n - ".join(results["fail"])
    print(summary)
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        rc = 2
    finally:
        # 清理临时数据库
        for ext in ("", "-wal", "-shm"):
            p = os.path.join(ROOT, "canteen_verify_tmp.db" + ext)
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
    sys.exit(rc)
