# 学校食堂食材管理系统

一款基于 PyQt6 开发的 Windows 单机版学校食堂食材管理软件，采用 macOS 风格 UI 设计。

## 功能模块

- **概览统计** - 食材总数、库存总值、低库存预警数
- **提醒中心** - 低库存提醒、过期预警、已过期食材
- **财务统计** - 月度收支、年度趋势、分类占比、供应商占比
- **食材管理** - 增删改查、Excel 导入导出
- **入库管理** - 入库记录、库存自动增加
- **出库管理** - 出库记录、库存自动扣减、库存不足拦截
- **库存盘点** - 系统库存 vs 实际库存、差异计算、自动校正
- **供应商管理** - 增删改查
- **分类管理** - 增删改查
- **系统设置** - 数据备份/恢复、修改密码
- **操作日志** - 全操作记录

## 默认登录信息

- 用户名: `admin`
- 密码: `admin123`

## 运行方式

### 方式一：直接运行可执行文件
双击 `学校食堂食材管理系统.exe` 即可运行。

### 方式二：Python 源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `学校食堂食材管理系统.exe` | Windows 可执行程序 |
| `main.py` | 主程序源码 |
| `database.py` | 数据库层源码 |
| `excel_handler.py` | Excel 导入导出源码 |
| `generate_template.py` | 导入模板生成器 |
| `full_test.py` | 全面自动化测试脚本（51项测试） |
| `食材导入模板.xlsx` | 食材导入模板 |
| `app_icon.ico` | 程序图标 |
| `requirements.txt` | Python 依赖清单 |

## 技术栈

- PyQt6 - GUI 框架
- SQLite3 - 本地数据库
- openpyxl - Excel 文件处理
- PyInstaller - 打包工具

## 数据存储

所有数据存储在程序同目录下的 `canteen.db` SQLite 数据库文件中。运行日志存储在 `logs/` 目录下。

## 安全特性

- SHA256 + 随机盐值密码哈希
- SQL 注入防护（字段白名单）
- 数据库连接上下文管理器
- 事务保护（BEGIN/COMMIT/ROLLBACK）

## GitHub 仓库

https://github.com/whblcy/school-canteen-management
