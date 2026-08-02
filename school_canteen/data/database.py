"""
数据库连接管理 - 基于 peewee ORM
替代原有的 sqlite3 手动连接管理，提供声明式模型操作
"""
from peewee import SqliteDatabase, DatabaseProxy
from ..config import get_config

# 延迟代理：允许在 models.py 中引用 db 而不需要在 import 时确定具体数据库
db = DatabaseProxy()


def get_database() -> SqliteDatabase:
    """获取实际的 SQLite 数据库实例"""
    cfg = get_config()
    return SqliteDatabase(
        str(cfg.paths.db_file),
        pragmas={
            "foreign_keys": 1,       # 开启外键约束
            "journal_mode": "wal",  # WAL 模式提升并发读性能
            "cache_size": -1024 * 64,  # 64MB 缓存
        },
    )


def initialize_database():
    """初始化数据库连接并创建表结构"""
    database = get_database()
    db.initialize(database)

    # 导入模型以触发表注册
    from . import models  # noqa: F401

    # 创建缺失的表（已有表不会重建）
    db.connect(reuse_if_open=True)
    db.create_tables(
        [
            models.User, models.Category, models.Supplier, models.Ingredient,
            models.StockIn, models.StockOut, models.InventoryCheck,
            models.OperationLog, models.CategoryMapping,
            models.InspectionRecord, models.Inspector,
        ],
        safe=True,
    )
    db.close()
