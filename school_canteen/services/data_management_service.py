"""
数据管理服务 - 备份、恢复、清理
业务规则: 数据清理需要二次确认（输入"确认删除"）
"""
import os
import shutil
from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from ..data.database import db, initialize_database
from ..data.models import seed_default_data
from ..data.repositories.report_repository import ReportRepository
from ..config import get_config
from ..core.exceptions import ValidationError
from ..core.session import Session
from ..utils.logging_config import get_logger

logger = get_logger()


class DataManagementService:
    """数据管理服务"""

    def __init__(self, report_repo: ReportRepository, log_repo=None):
        self.report_repo = report_repo
        self.log_repo = log_repo

    def backup_database(self, parent: QWidget = None) -> Optional[str]:
        """备份数据库"""
        cfg = get_config()
        default_name = f"canteen_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        file_path, _ = QFileDialog.getSaveFileName(
            parent, "选择备份位置", default_name, "Database Files (*.db)")
        if not file_path:
            return None
        try:
            # WAL 模式下未 checkpoint 的数据在 -wal 文件中，直接复制主文件会丢数据。
            # 先强制 checkpoint 把 WAL 合并回主库，再复制。
            try:
                db.execute_sql("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception:
                pass
            db.close()
            shutil.copy2(str(cfg.paths.db_file), file_path)
            logger.info(f"数据库已备份到: {file_path}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "数据库备份", "", 0, file_path)
            return file_path
        except Exception as e:
            logger.error(f"备份失败: {e}")
            raise

    def restore_database(self, backup_path: str, parent: QWidget = None) -> bool:
        """从备份恢复数据库"""
        cfg = get_config()
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")
        try:
            db.close()
            shutil.copy2(backup_path, str(cfg.paths.db_file))
            # 清除残留的 WAL/SHM，避免与新主文件不匹配导致数据错乱
            for suffix in ("-wal", "-shm"):
                p = str(cfg.paths.db_file) + suffix
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            initialize_database()
            logger.info(f"数据库已从备份恢复: {backup_path}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "数据库恢复", "", 0, backup_path)
            return True
        except Exception as e:
            logger.error(f"恢复失败: {e}")
            raise

    def clear_data(self, mode: str, confirm_phrase: str) -> bool:
        """
        清理数据
        mode: 'stock_records' | 'inventory' | 'all_data'
        confirm_phrase: 必须为 "确认删除" 才执行
        """
        cfg = get_config()
        if confirm_phrase != cfg.business.confirm_delete_phrase:
            raise ValidationError(f"请输入 '{cfg.business.confirm_delete_phrase}' 以确认")

        from ..data.database import db
        with db.atomic():
            if mode == "stock_records":
                self.report_repo.clear_stock_records()
                self.report_repo.clear_inspection_records()
                self.report_repo.reset_all_stock()
                logger.info("已清理出入库记录")
            elif mode == "inventory":
                self.report_repo.clear_inventory_records()
                self.report_repo.reset_all_stock()
                logger.info("已清理盘点记录")
            elif mode == "all_data":
                self.report_repo.clear_stock_records()
                self.report_repo.clear_inspection_records()
                self.report_repo.clear_inventory_records()
                self.report_repo.reset_all_stock()
                # 恢复默认数据
                seed_default_data()
                logger.info("已清理全部业务数据并恢复默认数据")
            else:
                raise ValidationError(f"未知的清理模式: {mode}")

        if self.log_repo:
            self.log_repo.add(Session.user_id, "数据清理", "", 0, f"模式={mode}")
        return True
