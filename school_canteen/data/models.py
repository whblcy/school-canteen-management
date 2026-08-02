"""
ORM 模型定义 - 使用 peewee 声明式模型
表结构兼容旧版 canteen.db，新增索引优化查询性能
"""
from peewee import (
    Model, TextField, IntegerField, FloatField,
    DateField, DateTimeField, ForeignKeyField,
    SQL,
)
from .database import db


class BaseModel(Model):
    """模型基类"""
    class Meta:
        database = db


class User(BaseModel):
    """用户表"""
    username = TextField(unique=True, null=False)
    password_hash = TextField(null=False)
    salt = TextField(null=False, default="")
    real_name = TextField(default="")
    role = TextField(default="user")
    status = IntegerField(default=1)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "users"
        indexes = ((("username",), True),)


class Category(BaseModel):
    """食材分类表"""
    name = TextField(unique=True, null=False)
    description = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "categories"


class Supplier(BaseModel):
    """供应商表"""
    name = TextField(null=False)
    contact_person = TextField(default="")
    phone = TextField(default="")
    address = TextField(default="")
    email = TextField(default="")
    status = IntegerField(default=1)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "suppliers"
        indexes = ((("name",), False),)


class Ingredient(BaseModel):
    """食材表"""
    name = TextField(null=False)
    category = ForeignKeyField(Category, backref="ingredients", null=True)
    unit = TextField(null=False)
    specification = TextField(default="")
    safety_stock = FloatField(default=0)
    current_stock = FloatField(default=0)
    supplier = ForeignKeyField(Supplier, backref="ingredients", null=True)
    status = IntegerField(default=1)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "ingredients"
        indexes = ((("name",), False), (("status",), False))


class StockIn(BaseModel):
    """入库记录表"""
    ingredient = ForeignKeyField(Ingredient, backref="stock_ins", null=False)
    quantity = FloatField(null=False)
    unit_price = FloatField(null=False)
    total_price = FloatField(null=False)
    supplier = ForeignKeyField(Supplier, backref="stock_ins", null=True)
    batch_number = TextField(default="")
    production_date = DateField(null=True)
    expiry_date = DateField(null=True)
    operator = TextField(default="")
    remark = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "stock_in"
        indexes = ((("ingredient",), False), (("created_at",), False),
                   (("expiry_date",), False), (("supplier",), False))


class StockOut(BaseModel):
    """出库记录表"""
    ingredient = ForeignKeyField(Ingredient, backref="stock_outs", null=False)
    quantity = FloatField(null=False)
    unit_price = FloatField(default=0)
    total_price = FloatField(default=0)
    purpose = TextField(default="")
    department = TextField(default="")
    operator = TextField(default="")
    remark = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "stock_out"
        indexes = ((("ingredient",), False), (("created_at",), False))


class InventoryCheck(BaseModel):
    """库存盘点表"""
    ingredient = ForeignKeyField(Ingredient, backref="checks", null=False)
    system_stock = FloatField(null=False)
    actual_stock = FloatField(null=False)
    difference = FloatField(null=False)
    operator = TextField(default="")
    remark = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "inventory_check"


class OperationLog(BaseModel):
    """操作日志表"""
    user = ForeignKeyField(User, backref="logs", null=True, on_delete="SET NULL")
    action = TextField(null=False)
    target_type = TextField(default="")
    target_id = IntegerField(default=0)
    details = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "operation_logs"
        indexes = ((("created_at",), False), (("user",), False))


class CategoryMapping(BaseModel):
    """类别映射表 - 外部类别名 → 系统分类"""
    source_category = TextField(unique=True, null=False)
    target_category = ForeignKeyField(Category, backref="mappings", null=False)
    description = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "category_mappings"


class InspectionRecord(BaseModel):
    """进货查验记录表 - 与入库记录一对一（stock_in_id 唯一）"""
    stock_in = ForeignKeyField(StockIn, backref="inspection", unique=True, null=True, on_delete="CASCADE")
    ingredient = ForeignKeyField(Ingredient, backref="inspections", null=False)
    quantity = FloatField(null=False)
    unit = TextField(null=False)
    production_date = DateField(null=True)
    shelf_life = TextField(default="")
    supplier_name = TextField(default="")
    supplier_address = TextField(default="")
    supplier_phone = TextField(default="")
    batch_number = TextField(default="")
    inspection_result = TextField(default="")
    inspector = TextField(default="")
    inspection_date = DateField(null=True)
    certificate_no = TextField(default="")
    remark = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "inspection_records"


class Inspector(BaseModel):
    """查验人员表"""
    name = TextField(unique=True, null=False)
    phone = TextField(default="")
    department = TextField(default="")
    status = IntegerField(default=1)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "inspectors"


def seed_default_data():
    """插入默认数据（分类、查验人员、类别映射、管理员）"""
    from ..config import get_config
    cfg = get_config()

    # 默认分类
    for name, desc in cfg.business.default_categories:
        Category.get_or_create(name=name, defaults={"description": desc})

    # 默认查验人员
    for name in cfg.business.default_inspectors:
        Inspector.get_or_create(name=name)

    # 默认类别映射
    default_mappings = [
        ("鸡肉类", "肉类"), ("蛋类", "蛋类"), ("蔬菜瓜果类", "蔬菜类"),
        ("干货类", "粮油类"), ("豆制品", "豆制品"), ("调味品", "调味品"),
        ("水产类", "水产类"), ("水果类", "水果类"), ("猪肉类", "肉类"),
        ("牛肉类", "肉类"), ("粮油类", "粮油类"), ("禽类", "肉类"),
        ("面食类", "粮油类"), ("乳制品", "蛋类"), ("速冻食品", "蔬菜类"),
        ("副食品", "调味品"),
    ]
    for source, target_name in default_mappings:
        cat = Category.get_or_none(Category.name == target_name)
        if cat:
            CategoryMapping.get_or_create(
                source_category=source,
                defaults={"target_category": cat}
            )

    # 默认管理员
    if not User.get_or_none(User.username == cfg.business.default_admin_username):
        from ..utils.security import hash_password
        password_hash, salt = hash_password(cfg.business.default_admin_password)
        User.create(
            username=cfg.business.default_admin_username,
            password_hash=password_hash,
            salt=salt,
            real_name=cfg.business.default_admin_real_name,
            role="admin",
        )
