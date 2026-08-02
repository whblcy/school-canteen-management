"""
查验服务 - 进货查验记录管理
业务规则: 一条入库记录对应一条查验记录（stock_in_id 唯一）
"""
from typing import List, Optional
from ..data.models import InspectionRecord, Inspector
from ..data.repositories.inspection_repository import InspectionRecordRepository, InspectorRepository
from ..data.repositories.stock_repository import StockInRepository
from ..core.exceptions import NotFoundError, ValidationError
from ..core.session import Session
from ..utils.logging_config import get_logger

logger = get_logger()


class InspectionService:
    """查验服务"""

    def __init__(self, inspection_repo: InspectionRecordRepository,
                 inspector_repo: InspectorRepository,
                 stock_in_repo: StockInRepository,
                 log_repo=None):
        self.inspection_repo = inspection_repo
        self.inspector_repo = inspector_repo
        self.stock_in_repo = stock_in_repo
        self.log_repo = log_repo

    def get_all_records(self, limit: int = 100) -> List[InspectionRecord]:
        return self.inspection_repo.get_all_with_ingredient(limit)

    def get_by_stock_in(self, stock_in_id: int) -> Optional[InspectionRecord]:
        return self.inspection_repo.get_by_stock_in_id(stock_in_id)

    def get_by_date_range(self, date_from: str, date_to: str) -> List[InspectionRecord]:
        """按日期范围查询，未查验的优先"""
        return self.inspection_repo.get_by_date_range(date_from, date_to)

    def upsert_record(self, stock_in_id: int, ingredient_id: int,
                      quantity: float, unit: str, **kwargs) -> InspectionRecord:
        """
        新增或更新查验记录
        业务规则: 按 stock_in_id 判断，存在则更新，否则新增
        """
        if not ingredient_id:
            raise ValidationError("食材不能为空")
        existing = self.inspection_repo.get_by_stock_in_id(stock_in_id)

        fields = dict(
            stock_in=stock_in_id, ingredient=ingredient_id,
            quantity=quantity, unit=unit,
            **{k: v for k, v in kwargs.items()
               if k in self.inspection_repo.ALLOWED_FIELDS and k != "stock_in"}
        )

        if existing:
            self.inspection_repo.update(existing.id, **fields)
            logger.info(f"更新查验记录: stock_in_id={stock_in_id}")
            return self.inspection_repo.get_by_id(existing.id)
        else:
            record = self.inspection_repo.create(**fields)
            logger.info(f"新增查验记录: stock_in_id={stock_in_id}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "新增查验记录", "inspection_record", record.id)
            return record

    def batch_save(self, records: List[dict]) -> tuple:
        """批量保存查验记录，返回 (新增数, 更新数)"""
        result = self.inspection_repo.batch_upsert(records)
        logger.info(f"批量保存查验记录: 新增 {result[0]} 条, 更新 {result[1]} 条")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "批量保存查验记录", "", 0,
                               f"新增{result[0]}条 更新{result[1]}条")
        return result

    def delete_record(self, id: int) -> bool:
        record = self.inspection_repo.get_by_id(id)
        if not record:
            raise NotFoundError("查验记录", id)
        result = self.inspection_repo.delete(id)
        if result:
            logger.info(f"删除查验记录: id={id}")
            if self.log_repo:
                self.log_repo.add(Session.user_id, "删除查验记录", "inspection_record", id)
        return result


class InspectorService:
    """查验人员服务"""

    def __init__(self, inspector_repo: InspectorRepository, log_repo=None):
        self.inspector_repo = inspector_repo
        self.log_repo = log_repo

    def get_all(self) -> List[Inspector]:
        return self.inspector_repo.get_all_ordered()

    def get_active(self) -> List[Inspector]:
        return self.inspector_repo.get_active()

    def get_names(self) -> list:
        return [i.name for i in self.inspector_repo.get_active()]

    def create(self, name: str, phone: str = "", department: str = "") -> Inspector:
        if not name or not name.strip():
            raise ValidationError("查验人姓名不能为空")
        if self.inspector_repo.get_by_name(name.strip()):
            raise ValidationError(f"查验人 '{name}' 已存在")
        inspector = self.inspector_repo.create(name=name.strip(), phone=phone, department=department)
        logger.info(f"新增查验人: {name}")
        return inspector

    def update(self, id: int, **kwargs) -> bool:
        result = self.inspector_repo.update(id, **kwargs)
        if result:
            logger.info(f"更新查验人: id={id}")
        return result

    def delete(self, id: int) -> bool:
        result = self.inspector_repo.delete(id)
        if result:
            logger.info(f"删除查验人: id={id}")
        return result
