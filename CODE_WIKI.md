# 学校食堂食材管理系统 - Code Wiki

> 一份结构化的代码知识库文档，覆盖项目整体架构、模块职责、关键类与函数、数据模型、依赖关系及运行方式。
> 适用于新成员快速理解系统、开发者定位实现细节以及维护者进行二次开发。

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈与依赖](#2-技术栈与依赖)
3. [整体架构](#3-整体架构)
4. [目录结构](#4-目录结构)
5. [模块职责详解](#5-模块职责详解)
   - 5.1 [main.py — UI 与业务编排层](#51-mainpy--ui-与业务编排层)
   - 5.2 [database.py — 数据层](#52-databasepy--数据层)
   - 5.3 [excel_handler.py — Excel 导入导出](#53-excel_handlerpy--excel-导入导出)
   - 5.4 [report_generator.py — 报表生成](#54-report_generatorpy--报表生成)
   - 5.5 [辅助脚本](#55-辅助脚本)
6. [数据库设计](#6-数据库设计)
7. [关键类与函数说明](#7-关键类与函数说明)
8. [核心业务流程](#8-核心业务流程)
9. [工程约定与安全特性](#9-工程约定与安全特性)
10. [运行方式](#10-运行方式)
11. [打包发布](#11-打包发布)
12. [测试](#12-测试)

---

## 1. 项目概述

**学校食堂食材管理系统** 是一款基于 PyQt6 开发的 Windows 单机版桌面应用，采用 macOS 风格 UI 设计，面向学校食堂的日常食材进销存与食品安全管理。

**核心能力：**

- 食材基础信息管理（增删改查、Excel 批量导入导出）
- 入库 / 出库管理（库存自动联动、批次与保质期管理）
- 食品安全管控（进货查验记录、过期食材出库拦截）
- 库存盘点（系统库存 vs 实际库存、差异自动校正）
- 财务与报表（月度收支、年度趋势、分类/供应商占比、监管报表导出）
- 提醒中心（低库存、过期预警、已过期食材）
- 系统管理（用户登录、数据备份/恢复、操作日志审计、数据清理）

**默认登录信息：**

- 用户名：`admin`
- 密码：`admin123`

**GitHub 仓库：** https://github.com/whblcy/school-canteen-management

---

## 2. 技术栈与依赖

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| PyQt6 | >=6.11.0 | GUI 框架，提供窗口、控件、信号槽机制 |
| openpyxl | >=3.1.5 | Excel（.xlsx）文件读写与样式处理 |
| pyinstaller | >=6.21.0 | 打包成 Windows 可执行文件 |

**运行时依赖（标准库）：** `sqlite3`、`os`、`hashlib`、`secrets`、`logging`、`shutil`、`traceback`、`dataclasses`、`contextlib`、`datetime`、`copy`。

依赖清单见 [requirements.txt](file:///c:/Users/lcy/work/school-canteen-management/requirements.txt)。

**运行环境要求：**

- Windows 10/11 64 位
- 屏幕分辨率建议 1920×1080 及以上
- 使用源码运行时需 Python 3.10+（推荐 3.12/3.14）

---

## 3. 整体架构

系统采用经典的**三层架构**，职责清晰分离：

```
┌─────────────────────────────────────────────────────────┐
│              表现层 (main.py)                            │
│   MainWindow · 各业务 Dialog/Widget · StyleSheet         │
│   负责：界面渲染、用户交互、业务流程编排                   │
└──────────────────────┬──────────────────────────────────┘
                       │ 调用
┌──────────────────────▼──────────────────────────────────┐
│              数据访问层 (database.py)                    │
│   DAO 类 · 数据模型 (dataclass) · 连接管理 · 密码哈希     │
│   负责：所有 SQL 操作、事务保护、数据校验                 │
└──────────────────────┬──────────────────────────────────┘
                       │ 读写
┌──────────────────────▼──────────────────────────────────┐
│           数据存储 (canteen.db / SQLite)                 │
│   11 张业务表 + 默认数据                                  │
└─────────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────┐
        │  工具层 (横向支撑)                  │
        │  excel_handler.py  Excel 导入导出   │
        │  report_generator.py 模板报表生成   │
        └─────────────────────────────────────┘
```

**设计要点：**

- **数据层与 UI 完全解耦**：所有数据库操作通过 DAO 类的静态方法访问，UI 层不直接写 SQL。
- **上下文管理器管理连接**：`get_connection()` 保证连接安全关闭，杜绝泄漏。
- **事务保护**：入库、出库、盘点等涉及库存联动的多步操作使用 `BEGIN/COMMIT/ROLLBACK`。
- **工具层横向复用**：Excel 处理与报表生成独立成模块，被多个 UI 组件调用。

---

## 4. 目录结构

```
school-canteen-management/
├── main.py                  # 主程序：UI + 业务编排（~4500 行）
├── database.py              # 数据层：schema + DAO + 数据模型（~1540 行）
├── excel_handler.py         # Excel 导入导出处理
├── report_generator.py      # 基于模板的监管报表生成
├── generate_template.py     # 独立脚本：生成食材导入模板
├── full_test.py             # 自动化测试脚本（51 项测试）
├── requirements.txt         # Python 依赖清单
├── app_icon.ico             # 程序图标
├── 食材导入模板.xlsx         # 食材批量导入模板
├── 表格/                    # 监管报表模板文件目录（运行时由 report_generator 读取）
├── build.bat                # PyInstaller 打包脚本
├── 打包说明.txt             # 交付包说明
├── README.md                # 项目说明
├── CHANGELOG.md             # 更新日志
├── CODE_WIKI.md             # 本文档
├── .gitignore
└── school-canteen-showcase/ # 项目展示页（HTML 静态站点）
    └── school-canteen-showcase.html
```

**运行时自动生成：**

- `canteen.db` — SQLite 数据库（所有业务数据）
- `logs/canteen_YYYYMMDD.log` — 按日轮转的运行日志

---

## 5. 模块职责详解

### 5.1 main.py — UI 与业务编排层

项目最大的模块，承载全部图形界面与业务流程编排。结构上分为四部分：

#### 5.1.1 基础设施

| 组件 | 行号 | 职责 |
|------|------|------|
| `get_resource_path()` | [main.py:13](file:///c:/Users/lcy/work/school-canteen-management/main.py#L13) | 兼容开发环境与 PyInstaller 打包环境的资源路径解析（`sys._MEIPASS`） |
| 日志配置 | [main.py:20-33](file:///c:/Users/lcy/work/school-canteen-management/main.py#L20) | 配置 `logging`，输出到 `logs/` 文件与 stdout |
| `StyleSheet` | [main.py:52](file:///c:/Users/lcy/work/school-canteen-management/main.py#L52) | 全局 macOS 风格 QSS 样式表（`MAIN_STYLE`），所有按钮/控件统一外观的来源 |

#### 5.1.2 对话框基类与登录

| 类 | 行号 | 职责 |
|----|------|------|
| `BaseDialog` | [main.py:300](file:///c:/Users/lcy/work/school-canteen-management/main.py#L300) | 所有业务对话框的基类。提供默认宽度 500px、统一样式、消息框工具方法（`show_error/show_warning/show_info/confirm`）以及表单辅助方法 `setup_form_field()`、`create_button_layout()` |
| `LoginDialog` | [main.py:344](file:///c:/Users/lcy/work/school-canteen-management/main.py#L344) | 登录窗口，调用 `UserDAO.authenticate()` 验证，成功后保存 `current_user` 供主窗口使用 |

> **注意**：`show_warning()` 返回 `None`，不可用于条件判断；需要确认结果时必须使用 `confirm()`。

#### 5.1.3 业务对话框（嵌入 QStackedWidget 的页面）

每个业务对话框既是对话框也是主界面中的一个"页面"，通过 `MainWindow` 的左侧导航栏切换。统一遵循"表单 + 表格"布局模式。

| 类 | 行号 | 对应业务 |
|----|------|----------|
| `CategoryDialog` | [main.py:527](file:///c:/Users/lcy/work/school-canteen-management/main.py#L527) | 食材分类管理（增删改查） |
| `CategoryMappingDialog` / `CategoryMappingEditDialog` | [main.py:619](file:///c:/Users/lcy/work/school-canteen-management/main.py#L619) / [main.py:710](file:///c:/Users/lcy/work/school-canteen-management/main.py#L710) | 外部类别名称 → 系统分类的映射管理（导入时使用） |
| `SupplierDialog` / `SupplierEditDialog` | [main.py:774](file:///c:/Users/lcy/work/school-canteen-management/main.py#L774) / [main.py:916](file:///c:/Users/lcy/work/school-canteen-management/main.py#L916) | 供应商管理（含搜索） |
| `IngredientDialog` / `IngredientEditDialog` | [main.py:976](file:///c:/Users/lcy/work/school-canteen-management/main.py#L976) / [main.py:1223](file:///c:/Users/lcy/work/school-canteen-management/main.py#L1223) | 食材管理（含批量删除、Excel 导入导出、模板下载） |
| `StockInDialog` | [main.py:1300](file:///c:/Users/lcy/work/school-canteen-management/main.py#L1300) | 入库管理：单条入库 + 销售订单 Excel 导入 |
| `InspectionRecordDialog` / `InspectionRecordEditDialog` | [main.py:1548](file:///c:/Users/lcy/work/school-canteen-management/main.py#L1548) / [main.py:2135](file:///c:/Users/lcy/work/school-canteen-management/main.py#L2135) | 进货查验记录管理（批量查验、可点击单元格下拉交互） |
| `StockOutDialog` | [main.py:2243](file:///c:/Users/lcy/work/school-canteen-management/main.py#L2243) | 出库管理：单条出库 + 批量出库（自动加载今日入库、加权平均单价） |
| `InventoryCheckDialog` | [main.py:2651](file:///c:/Users/lcy/work/school-canteen-management/main.py#L2651) | 库存盘点（系统 vs 实际、差异自动计算、批量盘点） |

#### 5.1.4 统计/展示型页面（QWidget）

| 类 | 行号 | 职责 |
|----|------|------|
| `ReportWidget` | [main.py:2944](file:///c:/Users/lcy/work/school-canteen-management/main.py#L2944) | 概览统计页：食材总数、库存总值、低库存预警数（统计卡片） |
| `FinanceWidget` | [main.py:3058](file:///c:/Users/lcy/work/school-canteen-management/main.py#L3058) | 财务统计页：月度收支、年度趋势、分类/供应商占比 |
| `AlertWidget` | [main.py:3210](file:///c:/Users/lcy/work/school-canteen-management/main.py#L3210) | 提醒中心：低库存、过期预警、已过期食材 |
| `SettingsWidget` | [main.py:3340](file:///c:/Users/lcy/work/school-canteen-management/main.py#L3340) | 系统设置：数据备份/恢复、查验人员管理、修改密码、数据清理（二次确认）。发射 `data_cleared` 信号触发全页面刷新 |
| `ReportExportWidget` | [main.py:3927](file:///c:/Users/lcy/work/school-canteen-management/main.py#L3927) | 报表导出页：非 Tab 布局，年/月选择器 + 多选报表 + 单目录批量导出 |

#### 5.1.5 主窗口与入口

| 类/函数 | 行号 | 职责 |
|--------|------|------|
| `MainWindow` | [main.py:4181](file:///c:/Users/lcy/work/school-canteen-management/main.py#L4181) | 主窗口：左侧导航栏（13 项）+ 右侧 `QStackedWidget` 内容区。聚合所有页面，提供 `refresh_all_pages()` 在数据清理后刷新全部 13 个页面 |
| `main()` | [main.py:4460](file:///c:/Users/lcy/work/school-canteen-management/main.py#L4460) | 程序入口：初始化数据库 → 创建 QApplication → 登录 → 显示主窗口 → 进入事件循环 |

**导航项顺序：** 概览统计、提醒中心、财务统计、食材管理、入库管理、出库管理、库存盘点、进货查验、报表导出、供应商管理、分类管理、类别映射、系统设置。

---

### 5.2 database.py — 数据层

[database.py](file:///c:/Users/lcy/work/school-canteen-management/database.py) 是唯一与 SQLite 交互的模块，包含四部分：

#### 5.2.1 连接与安全

| 函数 | 行号 | 说明 |
|------|------|------|
| `get_connection()` | [database.py:21](file:///c:/Users/lcy/work/school-canteen-management/database.py#L21) | 上下文管理器，设置 `row_factory=Row`、开启外键约束，`finally` 中关闭连接 |
| `hash_password()` | [database.py:33](file:///c:/Users/lcy/work/school-canteen-management/database.py#L33) | PBKDF2-HMAC-SHA256（迭代 100000 次）+ 随机盐值；兼容旧版 SHA256 |
| `verify_password()` | [database.py:42](file:///c:/Users/lcy/work/school-canteen-management/database.py#L42) | 先尝试 PBKDF2 验证，失败再回退旧版 SHA256 验证 |
| `init_database()` | [database.py:53](file:///c:/Users/lcy/work/school-canteen-management/database.py#L53) | 创建全部 11 张表、插入默认分类/查验人员/类别映射/管理员账号；含 `inspection_records.stock_in_id` 字段迁移逻辑 |

#### 5.2.2 数据模型（dataclass）

定义于 [database.py:320-453](file:///c:/Users/lcy/work/school-canteen-management/database.py#L320)，每个 dataclass 对应一张表，并附带联表查询所需的 `*_name` 字段：

`User`、`Category`、`Supplier`、`Ingredient`、`StockIn`、`StockOut`、`InventoryCheck`、`OperationLog`、`CategoryMapping`、`InspectionRecord`、`Inspector`。

#### 5.2.3 DAO 类

每个 DAO 提供静态方法（`get_all` / `add` / `update` / `delete` 等），UI 层通过类名调用。

| DAO | 行号 | 关键方法与业务规则 |
|-----|------|-------------------|
| `UserDAO` | [database.py:456](file:///c:/Users/lcy/work/school-canteen-management/database.py#L456) | `authenticate()` 登录验证；`delete()` 禁止删除 admin 角色 |
| `LogDAO` | [database.py:519](file:///c:/Users/lcy/work/school-canteen-management/database.py#L519) | `add()` 记录操作日志（含 user_id）；`get_by_action_keyword()` 按关键词检索 |
| `CategoryDAO` | [database.py:563](file:///c:/Users/lcy/work/school-canteen-management/database.py#L563) | 分类 CRUD |
| `SupplierDAO` | [database.py:608](file:///c:/Users/lcy/work/school-canteen-management/database.py#L608) | 供应商 CRUD；`update()` 使用 `ALLOWED_FIELDS` 白名单防注入 |
| `IngredientDAO` | [database.py:675](file:///c:/Users/lcy/work/school-canteen-management/database.py#L675) | 食材 CRUD；`get_low_stock()` 低库存查询；`update_stock()` 库存增减；`get_stock()` 查询当前库存 |
| `StockInDAO` | [database.py:787](file:///c:/Users/lcy/work/school-canteen-management/database.py#L787) | `add()` 事务：插入记录 + 更新库存，校验数量/单价非负；支持自定义 `created_at`（导入历史数据） |
| `StockOutDAO` | [database.py:852](file:///c:/Users/lcy/work/school-canteen-management/database.py#L852) | `add()` 事务：检查库存充足 + **过期食材拦截** + 扣减库存；`get_weighted_price()` 加权平均单价 `SUM(total_price)/SUM(quantity)` |
| `InventoryCheckDAO` | [database.py:942](file:///c:/Users/lcy/work/school-canteen-management/database.py#L942) | `add()` 事务：记录盘点差异 + 将库存校正为实际库存 |
| `ReportDAO` | [database.py:989](file:///c:/Users/lcy/work/school-canteen-management/database.py#L989) | 财务统计：`get_monthly_finance()`、`get_yearly_finance()`、`get_inventory_value()`（加权平均）、`get_expiry_warnings()`、`get_expired_items()` |
| `CategoryMappingDAO` | [database.py:1206](file:///c:/Users/lcy/work/school-canteen-management/database.py#L1206) | 类别映射 CRUD；`get_by_source()` 导入时查映射 |
| `InspectionRecordDAO` | [database.py:1271](file:///c:/Users/lcy/work/school-canteen-management/database.py#L1271) | 查验记录 CRUD；`get_by_stock_in_id()` 按入库记录查查验；`batch_add_or_update()` 批量保存（存在则更新，否则新增） |
| `InspectorDAO` | [database.py:1474](file:///c:/Users/lcy/work/school-canteen-management/database.py#L1474) | 查验人员 CRUD |

#### 5.2.4 SQL 注入防护

`SupplierDAO`、`IngredientDAO`、`InspectionRecordDAO`、`InspectorDAO` 的 `update()` 方法均采用 **字段白名单** 机制：只有 `ALLOWED_FIELDS` 集合中的字段名才允许拼入 SQL，从源头杜绝注入。

---

### 5.3 excel_handler.py — Excel 导入导出

[excel_handler.py](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py) 提供 `ExcelHandler` 类（全静态方法），负责与 Excel 文件的交互：

| 方法 | 行号 | 功能 |
|------|------|------|
| `export_ingredients()` | [excel_handler.py:74](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py#L74) | 导出食材余量信息（含库存不足高亮、汇总信息） |
| `import_ingredients()` | [excel_handler.py:162](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py#L162) | 导入食材（查重：库内重复 + 文件内重复；自动创建不存在的分类/供应商） |
| `create_template()` | [excel_handler.py:295](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py#L295) | 生成导入模板（含主模板页、填写说明页、分类参考页） |
| `export_stock_records()` | [excel_handler.py:474](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py#L474) | 导出入库/出库记录 |
| `import_sales_orders()` | [excel_handler.py:538](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py#L538) | **核心导入**：从销售订单 Excel 导入入库数据。处理合并单元格、多日期格式解析、同日同食材汇总、重复检测（新增/覆盖/跳过 三选一） |
| `import_inspection_records()` | [excel_handler.py:1012](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py#L1012) | 从进货查验记录表 Excel 导入 |

**模块级配置：** `DEFAULT_CATEGORY_MAP`（[excel_handler.py:14](file:///c:/Users/lcy/work/school-canteen-management/excel_handler.py#L14)）为外部类别名称到系统分类的默认映射；`get_category_map()` 优先从数据库读取，无则回退默认。

**样式常量：** `MAC_BLUE/GREEN/RED/ORANGE/GRAY/LIGHT_GRAY/BORDER` 定义 macOS 风格配色，统一应用于导出文件。

---

### 5.4 report_generator.py — 报表生成

[report_generator.py](file:///c:/Users/lcy/work/school-canteen-management/report_generator.py) 基于**预置 Excel 模板**生成监管报表，保证格式符合监管要求：

| 方法 | 行号 | 输出报表 | 模板文件 |
|------|------|----------|----------|
| `export_daily_stock_sheet()` | [report_generator.py:126](file:///c:/Users/lcy/work/school-canteen-management/report_generator.py#L126) | 每日出入库表（按天分 Sheet） | `2026年6月份每天出入库表.xlsx` |
| `export_monthly_summary()` | [report_generator.py:224](file:///c:/Users/lcy/work/school-canteen-management/report_generator.py#L224) | 每月出入库统计表 | `2026年6月每月出入库汇总等表和14、每月结算食材公示.xlsx` |
| `export_financial_report()` | [report_generator.py:314](file:///c:/Users/lcy/work/school-canteen-management/report_generator.py#L314) | 财务收支情况表（12 个月分 Sheet） | `附件1 ：月份、年度食堂（营养餐）财务收支情况表(1).xlsx` |
| `export_inventory_check_sheet()` | [report_generator.py:389](file:///c:/Users/lcy/work/school-canteen-management/report_generator.py#L389) | 库存物品盘存盘亏表 | `库存物品盘存盘亏表.xlsx` |
| `export_inspection_report()` | [report_generator.py:508](file:///c:/Users/lcy/work/school-canteen-management/report_generator.py#L508) | 进货查验记录表 | `进货查验记录表.xlsx` |

**核心辅助函数：**

- `get_template_dir()` / `get_template_path()` — 兼容打包环境的模板路径解析。
- `copy_cell_style()` / `insert_row_with_style()` / `copy_sheet_structure()` — 复制模板单元格样式、动态插入行并继承样式。
- `get_stock_in_by_date()` / `get_stock_out_by_date()` — 按日期聚合出入库数据（含加权平均单价）。
- `get_days_in_month()` — 计算某月天数。

**模板机制：** 先 `shutil.copy2` 复制模板，再用 `load_workbook` 打开填充数据；当数据行数超出模板预留行时，调用 `insert_row_with_style()` 动态扩行并继承上一行样式。

---

### 5.5 辅助脚本

| 脚本 | 说明 |
|------|------|
| [generate_template.py](file:///c:/Users/lcy/work/school-canteen-management/generate_template.py) | 独立运行脚本，生成 `食材导入模板.xlsx`（与 `ExcelHandler.create_template` 功能一致，字体用 Microsoft YaHei） |
| [full_test.py](file:///c:/Users/lcy/work/school-canteen-management/full_test.py) | 自动化测试脚本，覆盖 12 个模块共 51 项测试。运行前删除 `canteen.db` 从零开始测试 |
| [build.bat](file:///c:/Users/lcy/work/school-canteen-management/build.bat) | PyInstaller 打包脚本：清理 → 用 .spec 打包 → 压缩成 zip |

---

## 6. 数据库设计

数据库文件 `canteen.db`（SQLite），共 **11 张表**，开启外键约束。

### 6.1 表结构总览

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `users` | 用户 | username(唯一)、password_hash、salt、role、status |
| `categories` | 食材分类 | name(唯一) |
| `suppliers` | 供应商 | name、contact_person、phone、status |
| `ingredients` | 食材 | name、category_id→categories、unit、safety_stock、current_stock、supplier_id→suppliers |
| `stock_in` | 入库记录 | ingredient_id→ingredients、quantity、unit_price、total_price、batch_number、production_date、expiry_date、operator |
| `stock_out` | 出库记录 | ingredient_id→ingredients、quantity、unit_price、total_price、purpose、department、operator |
| `inventory_check` | 库存盘点 | ingredient_id→ingredients、system_stock、actual_stock、difference |
| `operation_logs` | 操作日志 | user_id→users、action、target_type、target_id、details |
| `category_mappings` | 类别映射 | source_category(唯一)、target_category_id→categories |
| `inspection_records` | 进货查验记录 | stock_in_id→stock_in(唯一)、ingredient_id→ingredients、inspection_result、inspector、certificate_no |
| `inspectors` | 查验人员 | name(唯一)、phone、department、status |

### 6.2 关键约束与关系

- `inspection_records.stock_in_id` 带 **UNIQUE 约束**（`idx_inspection_stock_in`）：一条入库记录只能对应一条查验记录。后续编辑走"存在则更新"逻辑。
- 外键关系：食材关联分类与供应商；入库/出库/盘点/查验均关联食材；日志关联用户。
- 迁移逻辑：`init_database()` 中检测旧库是否已有 `stock_in_id` 字段，缺失则 `ALTER TABLE` 添加并建唯一索引。

### 6.3 默认数据

- **8 个默认分类**：蔬菜类、肉类、水产类、豆制品、粮油类、调味品、蛋类、水果类
- **4 个默认查验人员**：张三、李四、王五、赵六
- **16 条默认类别映射**（如"鸡肉类"→"肉类"）
- **1 个默认管理员**：admin / admin123（PBKDF2 哈希）

---

## 7. 关键类与函数说明

### 7.1 核心业务方法

| 方法 | 位置 | 业务规则 |
|------|------|----------|
| `StockInDAO.add()` | [database.py:803](file:///c:/Users/lcy/work/school-canteen-management/database.py#L803) | 事务插入入库记录 + 增加库存；校验数量/单价非负；食材不存在则回滚 |
| `StockOutDAO.add()` | [database.py:882](file:///c:/Users/lcy/work/school-canteen-management/database.py#L882) | 事务出库：校验库存充足 → **拦截全部批次已过期食材** → 扣减库存；返回 `(bool, str)` |
| `StockOutDAO.get_weighted_price()` | [database.py:868](file:///c:/Users/lcy/work/school-canteen-management/database.py#L868) | 加权平均单价 = `SUM(total_price)/SUM(quantity)`，保证财务数据一致 |
| `InventoryCheckDAO.add()` | [database.py:958](file:///c:/Users/lcy/work/school-canteen-management/database.py#L958) | 事务：记录盘点差异 + 将库存校正为实际库存 |
| `InspectionRecordDAO.batch_add_or_update()` | [database.py:1361](file:///c:/Users/lcy/work/school-canteen-management/database.py#L1361) | 批量保存查验记录：按 stock_in_id 判断存在则 UPDATE 否则 INSERT |
| `ReportDAO.get_inventory_value()` | [database.py:1043](file:///c:/Users/lcy/work/school-canteen-management/database.py#L1043) | 库存总值 = Σ(当前库存 × 加权平均单价) |

### 7.2 UI 编排方法

| 方法 | 位置 | 说明 |
|------|------|------|
| `MainWindow.setup_ui()` | [main.py:4211](file:///c:/Users/lcy/work/school-canteen-management/main.py#L4211) | 构建左侧导航 + QStackedWidget，聚合 13 个页面 |
| `MainWindow.refresh_all_pages()` | [main.py:4426](file:///c:/Users/lcy/work/school-canteen-management/main.py#L4426) | 数据清理后刷新全部页面（由 `SettingsWidget.data_cleared` 信号触发） |
| `StockOutDialog.batch_stock_out()` | [main.py:2542](file:///c:/Users/lcy/work/school-canteen-management/main.py#L2542) | 批量出库：逐行校验，使用加权平均单价，记录成功/失败明细 |
| `ReportExportWidget.batch_export()` | [main.py:4132](file:///c:/Users/lcy/work/school-canteen-management/main.py#L4132) | 批量报表导出：单目录选择 + 自动命名 `[报表]_[年]年[月]月.xlsx` |
| `SettingsWidget.clear_data()` | [main.py:3711](file:///c:/Users/lcy/work/school-canteen-management/main.py#L3711) | 数据清理：**二次确认**（警告对话框 + 手动输入"确认删除"）；`all_data` 模式清理后重置自增 ID 并恢复默认数据 |

### 7.3 ExcelHandler 关键逻辑

- `import_sales_orders()` 支持四种重复处理：全部新增 / 全部覆盖 / 跳过重复 / 取消导入，并展示重复对比表。
- 日期解析 `parse_date()` 兼容 10+ 种格式（含中文"年月日"）。
- 同文件内同日同食材自动汇总数量与金额。

---

## 8. 核心业务流程

### 8.1 入库流程

```
用户填写表单 → StockInDialog.do_stock_in()
  → StockInDAO.add() [事务]
      ├─ INSERT stock_in (total_price = quantity × unit_price)
      └─ UPDATE ingredients SET current_stock += quantity
  → LogDAO.add("入库")
  → load_data() + load_ingredients() 刷新界面
```

### 8.2 出库流程（含食品安全拦截）

```
用户选择食材 + 数量 → StockOutDialog.do_stock_out() / batch_stock_out()
  → StockOutDAO.add() [事务]
      ├─ 检查库存是否充足
      ├─ 食品安全检查：所有批次是否已过期（全部过期则拦截）
      ├─ INSERT stock_out (单价=加权平均价)
      └─ UPDATE ingredients SET current_stock -= quantity
  → 返回 (success, msg)
```

### 8.3 进货查验流程

```
加载当月入库数据 → 用户在批量查验表中填写查验结果/查验人
  → InspectionRecordDialog.batch_save()
      → InspectionRecordDAO.batch_add_or_update()
          └─ 按 stock_in_id：存在则 UPDATE，否则 INSERT
```

> 查验结果列与查验人列采用**可点击单元格 + 下拉菜单**交互（蓝色字体 #0071e3、下拉箭头 ▼、手型光标）。

### 8.4 报表导出流程

```
ReportExportWidget 选择年/月 + 勾选报表 → 选择单一导出目录
  → 逐个调用 ReportGenerator.export_xxx()
      └─ 复制模板 → 填充数据 → 动态扩行
  → 文件名：[报表名称]_[年]年[月]月.xlsx 或 [报表名称]_[日期].xlsx
```

### 8.5 数据清理流程

```
SettingsWidget.clear_data()
  ├─ 第一步：警告对话框（HTML 风险提示）
  └─ 第二步：手动输入"确认删除" → 执行 DELETE
      └─ all_data 模式：重置 sqlite_sequence + init_database() 恢复默认数据
      └─ 发射 data_cleared 信号 → MainWindow.refresh_all_pages()
```

---

## 9. 工程约定与安全特性

### 9.1 安全特性

- **密码哈希**：PBKDF2-HMAC-SHA256 + 随机盐值（100000 次迭代），兼容旧版 SHA256。
- **SQL 注入防护**：`update()` 方法使用 `ALLOWED_FIELDS` 字段白名单。
- **连接管理**：`get_connection()` 上下文管理器保证连接关闭。
- **事务保护**：入库/出库/盘点等库存联动操作使用 `BEGIN/COMMIT/ROLLBACK`。
- **数据删除二次确认**：警告对话框 + 手动输入"确认删除"。
- **食品安全**：出库时拦截全部批次已过期的食材。

### 9.2 UI/UX 约定

- 所有按钮统一使用 `StyleSheet.MAIN_STYLE` 全局样式表。
- 按钮颜色编码：蓝（默认）、绿（成功）、橙（警告）、红（危险）、灰（次要）。
- 业务对话框继承 `BaseDialog`，默认宽 500px，表单字段最小宽 250px，按钮右对齐最小宽 80px。
- 管理对话框最小宽度 600-1100px，操作区间距 10px，行按钮间距 8px。
- 布局遵循"表单 + 表格"标准模式；报表导出页采用非 Tab 布局 + 顶部年/月选择器。
- 批量报表导出：单目录选择，自动命名 `[报表名称]_[年]年[月]月.xlsx`。

### 9.3 数据一致性约定

- 出库单价必须使用加权平均计算 `SUM(total_price)/SUM(quantity)`，禁止简单平均 `AVG(unit_price)`。
- 一条入库记录对应一条查验记录（stock_in_id 唯一），编辑查验走更新而非新增。
- 已查验记录在批量查验表中以绿色显示且默认不选中。
- 操作员字段应自动填充当前登录用户；日志须包含 user_id 以便追溯。

### 9.4 已知改进项

- 操作员字段目前未自动填充当前登录用户（仍为手动输入）。
- 日志的 `user_id` 当前传入 `None`，未绑定登录用户。
- 食材删除失败时静默处理，缺少明确反馈。

---

## 10. 运行方式

### 方式一：运行可执行文件

双击 `学校食堂食材管理系统.exe` 即可运行（无需安装 Python）。

### 方式二：源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 启动流程

1. `main()` 调用 `init_database()` 初始化数据库（建表 + 默认数据）。
2. 创建 `QApplication`，设置 Fusion 风格与微软雅黑字体。
3. 显示 `LoginDialog`，调用 `UserDAO.authenticate()` 验证登录。
4. 登录成功后创建 `MainWindow`（最大化显示），进入 Qt 事件循环。

### 数据存储位置

- 数据库：程序同目录下的 `canteen.db`
- 日志：程序同目录下的 `logs/canteen_YYYYMMDD.log`

---

## 11. 打包发布

使用 PyInstaller 打包，配置见 [build.bat](file:///c:/Users/lcy/work/school-canteen-management/build.bat)：

1. 清理 `build/dist/__pycache__` 临时目录。
2. 使用 `.spec` 文件执行 `pyinstaller --clean`（非单文件模式，确保资源文件正确加载）。
3. 将 `dist/学校食堂食材管理系统` 目录压缩为 `release/*.zip`。

> 打包后程序通过 `get_resource_path()` 兼容 `sys._MEIPASS` 临时目录，正确加载图标与报表模板。

---

## 12. 测试

[full_test.py](file:///c:/Users/lcy/work/school-canteen-management/full_test.py) 提供全面自动化测试：

- **覆盖范围**：12 个模块共 51 项测试。
- **测试策略**：运行前删除 `canteen.db`，从零初始化数据库后逐项验证。
- **涵盖内容**：数据库初始化、密码哈希、各 DAO 的 CRUD、入库库存联动、出库拦截、盘点校正、财务统计等。
- **运行方式**：`python full_test.py`，输出 `[PASS]/[FAIL]` 结果。

---

## 附录：模块依赖关系图

```
main.py
  ├─ imports → database (init_database, 各 DAO, get_connection)
  ├─ imports → excel_handler.ExcelHandler
  └─ imports → report_generator.ReportGenerator

excel_handler.py
  └─ imports → database (CategoryDAO, SupplierDAO, IngredientDAO,
                          StockInDAO, StockOutDAO, CategoryMappingDAO, get_connection)

report_generator.py
  └─ imports → database (CategoryDAO, SupplierDAO, IngredientDAO,
                          StockInDAO, StockOutDAO, InventoryCheckDAO,
                          ReportDAO, InspectionRecordDAO, get_connection)

generate_template.py    独立脚本，仅依赖 openpyxl
full_test.py            独立脚本，依赖 database 各 DAO
```

**依赖方向**：UI 层 → 数据层 ← 工具层；工具层不依赖 UI 层，可独立测试与复用。
