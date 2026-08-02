"""
库存服务 - 入库/出库/盘点核心业务规则
这是食品安全管控的核心：
- 出库时拦截全部批次已过期食材
- 出库单价使用加权平均计算
- 入库/出库/盘点均使用事务保证数据一致性
"""
from typing import List, Optional
from datetime import datetime

from ..data.models import StockIn, StockOut, InventoryCheck, Ingredient
from ..data.repositories.ingredient_repository import IngredientRepository
from ..data.repositories.stock_repository import (
    StockInRepository, StockOutRepository, InventoryCheckRepository
)
from ..data.repositories.catalog_repository import CategoryRepository, SupplierRepository
from ..data.database import db
from ..core.exceptions import (
    NotFoundError, ValidationError, BusinessRuleError,
    InsufficientStockError, ExpiredIngredientError,
)
from ..core.result import Result
from ..core.session import Session
from ..utils.logging_config import get_logger

logger = get_logger()


def _normalize_dt(value):
    """将 created_at 统一为 datetime 对象。

    peewee 的 DateTimeField 在写入字符串时不会自动转成 datetime，
    会导致库里混存 str 与 datetime 两种类型（Excel 导入路径历来如此）。
    这里在边界处显式归一，确保落库类型一致。
    无法解析时返回 None，由数据库默认值填充当前时间。
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
    return None


class StockService:
    """库存服务 - 核心业务规则所在"""

    def __init__(self,
                 ingredient_repo: IngredientRepository,
                 stock_in_repo: StockInRepository,
                 stock_out_repo: StockOutRepository,
                 inventory_repo: InventoryCheckRepository,
                 category_repo: CategoryRepository,
                 supplier_repo: SupplierRepository,
                 log_repo=None):
        self.ingredient_repo = ingredient_repo
        self.stock_in_repo = stock_in_repo
        self.stock_out_repo = stock_out_repo
        self.inventory_repo = inventory_repo
        self.category_repo = category_repo
        self.supplier_repo = supplier_repo
        self.log_repo = log_repo

    # ===== 入库 =====

    def stock_in(self, ingredient_id: int, quantity: float, unit_price: float,
                 supplier_id: int = None, batch_number: str = "",
                 production_date: str = None, expiry_date: str = None,
                 operator: str = "", remark: str = "",
                 created_at: str = None) -> StockIn:
        """
        入库操作 [事务]
        1. 校验数量/单价非负
        2. 插入入库记录
        3. 增加食材库存
        """
        if quantity <= 0:
            raise ValidationError("入库数量必须大于0")
        if unit_price < 0:
            raise ValidationError("单价不能为负数")

        ingredient = self.ingredient_repo.get_by_id(ingredient_id)
        if not ingredient:
            raise NotFoundError("食材", ingredient_id)

        total_price = quantity * unit_price
        kwargs = dict(
            ingredient=ingredient_id, quantity=quantity, unit_price=unit_price,
            total_price=total_price, batch_number=batch_number,
            production_date=production_date, expiry_date=expiry_date,
            operator=operator, remark=remark,
        )
        if supplier_id:
            kwargs["supplier"] = supplier_id
        # 仅特权角色（库存主管/管理员）可指定入库时间用于回溯录入；
        # 其余角色忽略该时间，使用系统当前时间，防止伪造历史记录
        if created_at and Session.can_set_custom_time:
            kwargs["created_at"] = _normalize_dt(created_at)
        else:
            # 普通角色忽略自定义时间，显式写入系统当前时间，
            # 避免 created_at 为 NULL 导致按日期/月份的报表漏统计
            kwargs["created_at"] = datetime.now()

        with db.atomic():
            record = self.stock_in_repo.create(**kwargs)
            self.ingredient_repo.update_stock(ingredient_id, quantity)

        logger.info(f"入库: {ingredient.name} x{quantity} @{unit_price}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "入库", "stock_in", record.id,
                               f"{ingredient.name} {quantity}{ingredient.unit}")
        return record

    def import_stock_in(self, product_name: str, quantity: float, unit_price: float,
                         unit: str = "", category_name: str = "", supplier_name: str = "",
                         batch_number: str = "", production_date: str = "",
                         expiry_date: str = "", operator: str = "",
                         created_at: str = None, remark: str = "",
                         check_duplicate: bool = True) -> Optional[StockIn]:
        """从 Excel 导入入库数据，自动创建食材。

        check_duplicate=True 时，若已存在完全相同的导入记录
        （同食材/数量/单价/发货日期/单据编号/来源备注）则返回 None 表示重复跳过，
        防止同一份文件重复导入导致库存/报表数据不断累加。
        """
        ingredient = self.ingredient_repo.get_by_name(product_name)
        if not ingredient:
            category_id = None
            if category_name:
                cat = self.category_repo.get_by_name(category_name)
                if not cat:
                    cat = self.category_repo.create(name=category_name)
                category_id = cat.id
            supplier_id = None
            if supplier_name:
                sup = self.supplier_repo.get_by_name(supplier_name)
                if not sup:
                    sup = self.supplier_repo.create(name=supplier_name)
                supplier_id = sup.id
            ingredient = self.ingredient_repo.create(
                name=product_name, category_id=category_id,
                unit=unit or "个", safety_stock=0, supplier_id=supplier_id,
            )

        if check_duplicate:
            date_str = None
            dt_obj = _normalize_dt(created_at) if created_at else None
            if dt_obj:
                date_str = dt_obj.strftime("%Y-%m-%d")
            if self.stock_in_repo.find_import_duplicate(
                ingredient.id, quantity, unit_price,
                batch_number=batch_number or "",
                remark=remark or "",
                date_str=date_str,
            ):
                logger.info(
                    f"跳过重复导入: {product_name} x{quantity} @{unit_price}"
                )
                return None

        return self.stock_in(
            ingredient.id, quantity, unit_price,
            supplier_id=ingredient.supplier_id if ingredient.supplier else None,
            batch_number=batch_number, production_date=production_date,
            expiry_date=expiry_date, operator=operator, remark=remark,
            created_at=created_at,
        )

    def get_stock_in_records(self, limit: int = 100) -> List[StockIn]:
        return self.stock_in_repo.get_all_with_ingredient(limit)

    def delete_stock_in(self, record_id: int) -> bool:
        """
        删除入库记录并回冲库存 [事务]
        删除后同步扣减对应食材库存，保持 库存 = Σ入库 − Σ出库 不变量。
        """
        record = self.stock_in_repo.get_by_id(record_id)
        if not record:
            raise NotFoundError("入库记录", record_id)
        ingredient_id = record.ingredient_id
        quantity = record.quantity

        with db.atomic():
            self.stock_in_repo.delete(record_id)
            self.ingredient_repo.update_stock(ingredient_id, -quantity)

        logger.info(f"删除入库记录: id={record_id}, 回冲库存 -{quantity}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "删除入库", "stock_in", record_id,
                               f"回冲库存 -{quantity}")
        return True

    # ===== 出库 =====

    def stock_out(self, ingredient_id: int, quantity: float,
                  purpose: str = "", department: str = "",
                  operator: str = "", remark: str = "",
                  created_at: str = None) -> StockOut:
        """
        出库操作 [事务]
        业务规则:
        1. 校验库存充足
        2. 食品安全: 拦截全部批次已过期食材（库存主管/管理员可绕过）
        3. 单价使用加权平均计算
        4. 扣减库存
        5. created_at 仅特权角色可指定（用于回溯录入历史出库）
        """
        if quantity <= 0:
            raise ValidationError("出库数量必须大于0")

        ingredient = self.ingredient_repo.get_by_id(ingredient_id)
        if not ingredient:
            raise NotFoundError("食材", ingredient_id)

        current_stock = ingredient.current_stock
        if current_stock < quantity:
            raise InsufficientStockError(ingredient.name, current_stock, quantity)

        # 食品安全: 检查是否有未过期批次
        # 特权角色（库存主管/管理员）可绕过该拦截，用于合法的特殊出库
        if not Session.can_bypass_expiry and self.stock_in_repo.has_any_batches(ingredient_id):
            if not self.stock_in_repo.has_unexpired_batches(ingredient_id):
                raise ExpiredIngredientError(ingredient.name)

        # 加权平均单价
        unit_price = self.stock_in_repo.get_weighted_price(ingredient_id)
        total_price = quantity * unit_price

        kwargs = dict(
            ingredient=ingredient_id, quantity=quantity,
            unit_price=unit_price, total_price=total_price,
            purpose=purpose, department=department,
            operator=operator, remark=remark,
        )
        # 仅特权角色可指定出库时间；其余角色忽略，使用当前时间
        if created_at and Session.can_set_custom_time:
            kwargs["created_at"] = _normalize_dt(created_at)
        else:
            # 显式写入系统当前时间，避免 created_at 为 NULL 导致报表漏统计
            kwargs["created_at"] = datetime.now()

        with db.atomic():
            record = self.stock_out_repo.create(**kwargs)
            self.ingredient_repo.update_stock(ingredient_id, -quantity)

        logger.info(f"出库: {ingredient.name} x{quantity} @{unit_price}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "出库", "stock_out", record.id,
                               f"{ingredient.name} {quantity}{ingredient.unit}")
        return record

    def batch_stock_out(self, items: List[dict]) -> Result:
        """
        批量出库
        items: [{ingredient_id, quantity, purpose, department, operator, remark}]
        返回: Result(success, message, data={success_count, fail_count, errors})
        """
        success_count = 0
        fail_count = 0
        errors = []

        for item in items:
            try:
                self.stock_out(
                    ingredient_id=item["ingredient_id"],
                    quantity=item["quantity"],
                    purpose=item.get("purpose", ""),
                    department=item.get("department", ""),
                    operator=item.get("operator", ""),
                    remark=item.get("remark", ""),
                    created_at=item.get("created_at"),
                )
                success_count += 1
            except (BusinessRuleError, ValidationError, NotFoundError) as e:
                fail_count += 1
                ing_name = item.get("ingredient_name", f"id={item['ingredient_id']}")
                errors.append(f"{ing_name}: {str(e)}")
            except Exception as e:
                fail_count += 1
                errors.append(f"未知错误: {str(e)}")
                logger.exception(f"批量出库异常: {e}")

        if fail_count == 0:
            return Result.ok(
                data={"success_count": success_count, "fail_count": fail_count, "errors": errors},
                message=f"批量出库成功，共 {success_count} 条",
            )
        return Result.fail(
            message=f"成功 {success_count} 条，失败 {fail_count} 条",
            data={"success_count": success_count, "fail_count": fail_count, "errors": errors},
        )

    def get_stock_out_records(self, limit: int = 100) -> List[StockOut]:
        return self.stock_out_repo.get_all_with_ingredient(limit)

    def delete_stock_out(self, record_id: int) -> bool:
        """
        删除出库记录并回冲库存 [事务]
        出库当初扣减了库存，删除后应加回，保持库存不变量。
        """
        record = self.stock_out_repo.get_by_id(record_id)
        if not record:
            raise NotFoundError("出库记录", record_id)
        ingredient_id = record.ingredient_id
        quantity = record.quantity

        with db.atomic():
            self.stock_out_repo.delete(record_id)
            self.ingredient_repo.update_stock(ingredient_id, quantity)

        logger.info(f"删除出库记录: id={record_id}, 回冲库存 +{quantity}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "删除出库", "stock_out", record_id,
                               f"回冲库存 +{quantity}")
        return True

    def get_weighted_price(self, ingredient_id: int) -> float:
        """获取食材加权平均单价"""
        return self.stock_in_repo.get_weighted_price(ingredient_id)

    # ===== 盘点 =====

    def inventory_check(self, ingredient_id: int, actual_stock: float,
                        operator: str = "", remark: str = "") -> InventoryCheck:
        """
        库存盘点 [事务]
        1. 记录系统库存 vs 实际库存差异
        2. 将库存校正为实际库存
        """
        ingredient = self.ingredient_repo.get_by_id(ingredient_id)
        if not ingredient:
            raise NotFoundError("食材", ingredient_id)

        system_stock = ingredient.current_stock
        difference = actual_stock - system_stock

        with db.atomic():
            record = self.inventory_repo.create(
                ingredient=ingredient_id, system_stock=system_stock,
                actual_stock=actual_stock, difference=difference,
                operator=operator, remark=remark,
            )
            self.ingredient_repo.set_stock(ingredient_id, actual_stock)

        logger.info(f"盘点: {ingredient.name} 系统={system_stock} 实际={actual_stock} 差异={difference}")
        if self.log_repo:
            self.log_repo.add(Session.user_id, "库存盘点", "inventory_check", record.id,
                               f"{ingredient.name} 差异={difference}")
        return record

    def batch_inventory_check(self, items: List[dict]) -> int:
        """批量盘点，返回成功数量"""
        count = 0
        for item in items:
            try:
                self.inventory_check(
                    ingredient_id=item["ingredient_id"],
                    actual_stock=item["actual_stock"],
                    operator=item.get("operator", ""),
                    remark=item.get("remark", ""),
                )
                count += 1
            except Exception as e:
                logger.warning(f"盘点失败: {e}")
        return count

    def get_inventory_records(self, limit: int = 100) -> List[InventoryCheck]:
        return self.inventory_repo.get_all_with_ingredient(limit)
