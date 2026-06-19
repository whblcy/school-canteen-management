"""
数据库模型和连接管理 - 完整版
修复内容:
1. 使用上下文管理器保证连接关闭
2. 修复SQL注入漏洞（字段名白名单校验）
3. 多步操作使用事务保护
4. 密码使用SHA256+盐值增强安全性
"""
import sqlite3
import os
import hashlib
import secrets
from dataclasses import dataclass
from typing import List, Optional, Tuple
from contextlib import contextmanager


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'canteen.db')


@contextmanager
def get_connection():
    """获取数据库连接（上下文管理器，确保连接关闭）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """密码哈希: SHA256 + 盐值"""
    if salt is None:
        salt = secrets.token_hex(16)
    salted = f"{password}{salt}"
    password_hash = hashlib.sha256(salted.encode()).hexdigest()
    return password_hash, salt


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """验证密码"""
    salted = f"{password}{salt}"
    return hashlib.sha256(salted.encode()).hexdigest() == password_hash


def init_database():
    """初始化数据库表结构"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 用户表 (增加salt字段)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                real_name TEXT,
                role TEXT DEFAULT 'user',
                status INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 食材分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 供应商表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                address TEXT,
                email TEXT,
                status INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 食材表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER,
                unit TEXT NOT NULL,
                specification TEXT,
                safety_stock REAL DEFAULT 0,
                current_stock REAL DEFAULT 0,
                supplier_id INTEGER,
                status INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        
        # 入库记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_in (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                supplier_id INTEGER,
                batch_number TEXT,
                production_date DATE,
                expiry_date DATE,
                operator TEXT,
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        
        # 出库记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_out (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL,
                total_price REAL,
                purpose TEXT,
                department TEXT,
                operator TEXT,
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            )
        ''')
        
        # 库存盘点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_check (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                system_stock REAL NOT NULL,
                actual_stock REAL NOT NULL,
                difference REAL NOT NULL,
                operator TEXT,
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            )
        ''')
        
        # 操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认分类
        default_categories = [
            ('蔬菜类', '各类新鲜蔬菜'),
            ('肉类', '猪肉、牛肉、鸡肉等'),
            ('水产类', '鱼、虾、蟹等'),
            ('豆制品', '豆腐、豆皮等'),
            ('粮油类', '米、面、油等'),
            ('调味品', '盐、糖、酱油等'),
            ('蛋类', '鸡蛋、鸭蛋等'),
            ('水果类', '各类水果')
        ]
        
        for name, desc in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)
            ''', (name, desc))
        
        # 插入默认管理员账号 (密码: admin123)
        # 先检查是否已存在
        cursor.execute("SELECT id FROM users WHERE username = ?", ('admin',))
        if not cursor.fetchone():
            password_hash, salt = hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, real_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', password_hash, salt, '系统管理员', 'admin'))
        
        conn.commit()


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    salt: str = ""
    real_name: str = ""
    role: str = "user"
    status: int = 1
    created_at: str = ""


@dataclass
class Category:
    id: int
    name: str
    description: str = ""
    created_at: str = ""


@dataclass
class Supplier:
    id: int
    name: str
    contact_person: str = ""
    phone: str = ""
    address: str = ""
    email: str = ""
    status: int = 1
    created_at: str = ""


@dataclass
class Ingredient:
    id: int
    name: str
    category_id: int
    unit: str
    specification: str = ""
    safety_stock: float = 0
    current_stock: float = 0
    supplier_id: Optional[int] = None
    status: int = 1
    created_at: str = ""
    category_name: str = ""
    supplier_name: str = ""


@dataclass
class StockIn:
    id: int
    ingredient_id: int
    quantity: float
    unit_price: float
    total_price: float
    supplier_id: Optional[int] = None
    batch_number: str = ""
    production_date: str = ""
    expiry_date: str = ""
    operator: str = ""
    remark: str = ""
    created_at: str = ""
    ingredient_name: str = ""


@dataclass
class StockOut:
    id: int
    ingredient_id: int
    quantity: float
    unit_price: float = 0
    total_price: float = 0
    purpose: str = ""
    department: str = ""
    operator: str = ""
    remark: str = ""
    created_at: str = ""
    ingredient_name: str = ""


@dataclass
class InventoryCheck:
    id: int
    ingredient_id: int
    system_stock: float
    actual_stock: float
    difference: float
    operator: str = ""
    remark: str = ""
    created_at: str = ""
    ingredient_name: str = ""


@dataclass
class OperationLog:
    id: int
    user_id: Optional[int]
    action: str
    target_type: str = ""
    target_id: int = 0
    details: str = ""
    created_at: str = ""


class UserDAO:
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE username = ? AND status = 1
            ''', (username,))
            row = cursor.fetchone()
            if not row:
                return None
            user = User(**dict(row))
            if verify_password(password, user.salt, user.password_hash):
                return user
            return None
    
    @staticmethod
    def get_all() -> List[User]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY username")
            rows = cursor.fetchall()
            return [User(**dict(row)) for row in rows]
    
    @staticmethod
    def add(username: str, password: str, real_name: str = "", role: str = "user") -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                password_hash, salt = hash_password(password)
                cursor.execute('''
                    INSERT INTO users (username, password_hash, salt, real_name, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password_hash, salt, real_name, role))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    @staticmethod
    def update_password(user_id: int, new_password: str) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            password_hash, salt = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (password_hash, salt, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(user_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
            conn.commit()
            return cursor.rowcount > 0


class LogDAO:
    @staticmethod
    def add(user_id: Optional[int], action: str, target_type: str = "", target_id: int = 0, details: str = ""):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_logs (user_id, action, target_type, target_id, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, action, target_type, target_id, details))
            conn.commit()
    
    @staticmethod
    def get_all(limit: int = 500) -> List[OperationLog]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.*, u.username, u.real_name
                FROM operation_logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [OperationLog(**{k: v for k, v in dict(row).items() if k in OperationLog.__dataclass_fields__}) for row in rows]


class CategoryDAO:
    @staticmethod
    def get_all() -> List[Category]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name")
            rows = cursor.fetchall()
            return [Category(**dict(row)) for row in rows]
    
    @staticmethod
    def add(name: str, description: str = "") -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                             (name, description))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    @staticmethod
    def update(id: int, name: str, description: str = "") -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE categories SET name=?, description=? WHERE id=?",
                             (name, description, id))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False
    
    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM categories WHERE id=?", (id,))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False


class SupplierDAO:
    # 允许的更新字段（防止SQL注入）
    ALLOWED_FIELDS = {'name', 'contact_person', 'phone', 'address', 'email', 'status'}
    
    @staticmethod
    def get_all() -> List[Supplier]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers ORDER BY name")
            rows = cursor.fetchall()
            return [Supplier(**dict(row)) for row in rows]
    
    @staticmethod
    def get_active() -> List[Supplier]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE status=1 ORDER BY name")
            rows = cursor.fetchall()
            return [Supplier(**dict(row)) for row in rows]
    
    @staticmethod
    def add(name: str, contact_person: str = "", phone: str = "", 
            address: str = "", email: str = "") -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO suppliers (name, contact_person, phone, address, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, contact_person, phone, address, email))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def update(id: int, **kwargs) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in SupplierDAO.ALLOWED_FIELDS:
                    fields.append(f"{key}=?")
                    values.append(value)
            if not fields:
                return False
            values.append(id)
            cursor.execute(f"UPDATE suppliers SET {', '.join(fields)} WHERE id=?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM suppliers WHERE id=?", (id,))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False


class IngredientDAO:
    ALLOWED_FIELDS = {'name', 'category_id', 'unit', 'specification', 
                      'safety_stock', 'current_stock', 'supplier_id', 'status'}
    
    @staticmethod
    def get_all() -> List[Ingredient]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, c.name as category_name, s.name as supplier_name
                FROM ingredients i
                LEFT JOIN categories c ON i.category_id = c.id
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                ORDER BY i.name
            ''')
            rows = cursor.fetchall()
            return [Ingredient(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(id: int) -> Optional[Ingredient]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, c.name as category_name, s.name as supplier_name
                FROM ingredients i
                LEFT JOIN categories c ON i.category_id = c.id
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                WHERE i.id = ?
            ''', (id,))
            row = cursor.fetchone()
            return Ingredient(**dict(row)) if row else None
    
    @staticmethod
    def get_low_stock() -> List[Ingredient]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, c.name as category_name, s.name as supplier_name
                FROM ingredients i
                LEFT JOIN categories c ON i.category_id = c.id
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                WHERE i.current_stock <= i.safety_stock AND i.status = 1
                ORDER BY i.name
            ''')
            rows = cursor.fetchall()
            return [Ingredient(**dict(row)) for row in rows]
    
    @staticmethod
    def add(name: str, category_id: int, unit: str, specification: str = "",
            safety_stock: float = 0, supplier_id: Optional[int] = None) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ingredients (name, category_id, unit, specification, safety_stock, supplier_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, category_id, unit, specification, safety_stock, supplier_id))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def update(id: int, **kwargs) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in IngredientDAO.ALLOWED_FIELDS:
                    fields.append(f"{key}=?")
                    values.append(value)
            if not fields:
                return False
            values.append(id)
            cursor.execute(f"UPDATE ingredients SET {', '.join(fields)} WHERE id=?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM ingredients WHERE id=?", (id,))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                return False
    
    @staticmethod
    def update_stock(id: int, quantity: float) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE ingredients SET current_stock = current_stock + ? WHERE id=?",
                          (quantity, id))
            conn.commit()
            return cursor.rowcount > 0


class StockInDAO:
    @staticmethod
    def get_all(limit: int = 100) -> List[StockIn]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT si.*, i.name as ingredient_name
                FROM stock_in si
                JOIN ingredients i ON si.ingredient_id = i.id
                ORDER BY si.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [StockIn(**dict(row)) for row in rows]
    
    @staticmethod
    def add(ingredient_id: int, quantity: float, unit_price: float,
            supplier_id: Optional[int] = None, batch_number: str = "",
            production_date: str = "", expiry_date: str = "",
            operator: str = "", remark: str = "") -> int:
        if quantity < 0 or unit_price < 0:
            raise ValueError("数量和单价不能为负数")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            total_price = quantity * unit_price
            
            try:
                cursor.execute("BEGIN")
                
                cursor.execute('''
                    INSERT INTO stock_in (ingredient_id, quantity, unit_price, total_price,
                                        supplier_id, batch_number, production_date, expiry_date,
                                        operator, remark)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ingredient_id, quantity, unit_price, total_price, supplier_id,
                      batch_number, production_date, expiry_date, operator, remark))
                
                last_id = cursor.lastrowid
                
                # 更新库存
                cursor.execute("UPDATE ingredients SET current_stock = current_stock + ? WHERE id=?",
                              (quantity, ingredient_id))
                
                if cursor.rowcount == 0:
                    conn.rollback()
                    raise ValueError("食材不存在，库存更新失败")
                
                conn.commit()
                return last_id
            except Exception:
                conn.rollback()
                raise


class StockOutDAO:
    @staticmethod
    def get_all(limit: int = 100) -> List[StockOut]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT so.*, i.name as ingredient_name
                FROM stock_out so
                JOIN ingredients i ON so.ingredient_id = i.id
                ORDER BY so.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [StockOut(**dict(row)) for row in rows]
    
    @staticmethod
    def add(ingredient_id: int, quantity: float, unit_price: float = 0,
            purpose: str = "", department: str = "", operator: str = "",
            remark: str = "") -> Tuple[bool, str]:
        if quantity < 0:
            return False, "出库数量不能为负数"
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("BEGIN")
                
                # 检查库存
                cursor.execute("SELECT current_stock FROM ingredients WHERE id=?", (ingredient_id,))
                row = cursor.fetchone()
                if not row:
                    conn.rollback()
                    return False, "食材不存在"
                
                current_stock = row['current_stock']
                if current_stock < quantity:
                    conn.rollback()
                    return False, f"库存不足，当前库存: {current_stock}"
                
                total_price = quantity * unit_price
                
                cursor.execute('''
                    INSERT INTO stock_out (ingredient_id, quantity, unit_price, total_price,
                                         purpose, department, operator, remark)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ingredient_id, quantity, unit_price, total_price, purpose,
                      department, operator, remark))
                
                # 更新库存
                cursor.execute("UPDATE ingredients SET current_stock = current_stock - ? WHERE id=?",
                              (quantity, ingredient_id))
                
                conn.commit()
                return True, "出库成功"
            except Exception:
                conn.rollback()
                raise


class InventoryCheckDAO:
    @staticmethod
    def get_all(limit: int = 100) -> List[InventoryCheck]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ic.*, i.name as ingredient_name
                FROM inventory_check ic
                JOIN ingredients i ON ic.ingredient_id = i.id
                ORDER BY ic.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [InventoryCheck(**dict(row)) for row in rows]
    
    @staticmethod
    def add(ingredient_id: int, system_stock: float, actual_stock: float,
            operator: str = "", remark: str = "") -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            difference = actual_stock - system_stock
            
            try:
                cursor.execute("BEGIN")
                
                cursor.execute('''
                    INSERT INTO inventory_check (ingredient_id, system_stock, actual_stock, difference, operator, remark)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ingredient_id, system_stock, actual_stock, difference, operator, remark))
                
                last_id = cursor.lastrowid
                
                # 更新库存为实际库存
                cursor.execute("UPDATE ingredients SET current_stock = ? WHERE id=?",
                              (actual_stock, ingredient_id))
                
                if cursor.rowcount == 0:
                    conn.rollback()
                    raise ValueError("食材不存在，库存更新失败")
                
                conn.commit()
                return last_id
            except Exception:
                conn.rollback()
                raise


class ReportDAO:
    @staticmethod
    def get_stock_summary() -> List[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.name as category_name,
                       COUNT(i.id) as ingredient_count,
                       SUM(i.current_stock) as total_stock,
                       SUM(i.safety_stock) as total_safety_stock
                FROM ingredients i
                JOIN categories c ON i.category_id = c.id
                WHERE i.status = 1
                GROUP BY c.id
                ORDER BY c.name
            ''')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_monthly_in(year: int, month: int) -> List[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.name as ingredient_name,
                       SUM(si.quantity) as total_quantity,
                       SUM(si.total_price) as total_amount
                FROM stock_in si
                JOIN ingredients i ON si.ingredient_id = i.id
                WHERE strftime('%Y', si.created_at) = ? AND strftime('%m', si.created_at) = ?
                GROUP BY si.ingredient_id
                ORDER BY total_amount DESC
            ''', (str(year), f"{month:02d}"))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_monthly_out(year: int, month: int) -> List[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.name as ingredient_name,
                       SUM(so.quantity) as total_quantity,
                       SUM(so.total_price) as total_amount
                FROM stock_out so
                JOIN ingredients i ON so.ingredient_id = i.id
                WHERE strftime('%Y', so.created_at) = ? AND strftime('%m', so.created_at) = ?
                GROUP BY so.ingredient_id
                ORDER BY total_amount DESC
            ''', (str(year), f"{month:02d}"))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_inventory_value() -> float:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(i.current_stock * COALESCE(
                    (SELECT unit_price FROM stock_in WHERE ingredient_id = i.id ORDER BY created_at DESC LIMIT 1),
                    0
                )) as total_value
                FROM ingredients i
                WHERE i.status = 1
            ''')
            row = cursor.fetchone()
            return row['total_value'] or 0

    @staticmethod
    def get_monthly_finance(year: int, month: int) -> dict:
        """获取月度财务统计"""
        with get_connection() as conn:
            cursor = conn.cursor()

            # 入库总支出
            cursor.execute('''
                SELECT COALESCE(SUM(total_price), 0) as total_in
                FROM stock_in
                WHERE strftime('%Y', created_at) = ? AND strftime('%m', created_at) = ?
            ''', (str(year), f"{month:02d}"))
            total_in = cursor.fetchone()['total_in'] or 0

            # 出库总成本
            cursor.execute('''
                SELECT COALESCE(SUM(total_price), 0) as total_out
                FROM stock_out
                WHERE strftime('%Y', created_at) = ? AND strftime('%m', created_at) = ?
            ''', (str(year), f"{month:02d}"))
            total_out = cursor.fetchone()['total_out'] or 0

            # 按分类统计入库金额
            cursor.execute('''
                SELECT c.name as category_name, SUM(si.total_price) as amount
                FROM stock_in si
                JOIN ingredients i ON si.ingredient_id = i.id
                JOIN categories c ON i.category_id = c.id
                WHERE strftime('%Y', si.created_at) = ? AND strftime('%m', si.created_at) = ?
                GROUP BY c.id
                ORDER BY amount DESC
            ''', (str(year), f"{month:02d}"))
            category_in = [dict(row) for row in cursor.fetchall()]

            # 按分类统计出库金额
            cursor.execute('''
                SELECT c.name as category_name, SUM(so.total_price) as amount
                FROM stock_out so
                JOIN ingredients i ON so.ingredient_id = i.id
                JOIN categories c ON i.category_id = c.id
                WHERE strftime('%Y', so.created_at) = ? AND strftime('%m', so.created_at) = ?
                GROUP BY c.id
                ORDER BY amount DESC
            ''', (str(year), f"{month:02d}"))
            category_out = [dict(row) for row in cursor.fetchall()]

            # 按供应商统计采购金额
            cursor.execute('''
                SELECT s.name as supplier_name, SUM(si.total_price) as amount
                FROM stock_in si
                JOIN suppliers s ON si.supplier_id = s.id
                WHERE strftime('%Y', si.created_at) = ? AND strftime('%m', si.created_at) = ?
                GROUP BY si.supplier_id
                ORDER BY amount DESC
            ''', (str(year), f"{month:02d}"))
            supplier_amount = [dict(row) for row in cursor.fetchall()]

            return {
                'total_in': total_in,
                'total_out': total_out,
                'category_in': category_in,
                'category_out': category_out,
                'supplier_amount': supplier_amount
            }

    @staticmethod
    def get_yearly_finance(year: int) -> List[dict]:
        """获取年度月度财务趋势"""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 
                    strftime('%m', created_at) as month,
                    COALESCE(SUM(total_price), 0) as amount
                FROM stock_in
                WHERE strftime('%Y', created_at) = ?
                GROUP BY strftime('%m', created_at)
                ORDER BY month
            ''', (str(year),))
            in_data = {row['month']: row['amount'] for row in cursor.fetchall()}

            cursor.execute('''
                SELECT 
                    strftime('%m', created_at) as month,
                    COALESCE(SUM(total_price), 0) as amount
                FROM stock_out
                WHERE strftime('%Y', created_at) = ?
                GROUP BY strftime('%m', created_at)
                ORDER BY month
            ''', (str(year),))
            out_data = {row['month']: row['amount'] for row in cursor.fetchall()}

        result = []
        for m in range(1, 13):
            month_str = f"{m:02d}"
            result.append({
                'month': m,
                'month_name': f"{m}月",
                'in_amount': in_data.get(month_str, 0),
                'out_amount': out_data.get(month_str, 0)
            })
        return result

    @staticmethod
    def get_expiry_warnings(days: int = 7) -> List[dict]:
        """获取即将过期的食材预警"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT si.id, i.name as ingredient_name, si.batch_number,
                       si.quantity, si.expiry_date, si.created_at,
                       julianday(si.expiry_date) - julianday('now') as days_left
                FROM stock_in si
                JOIN ingredients i ON si.ingredient_id = i.id
                WHERE si.expiry_date IS NOT NULL
                  AND si.expiry_date != ''
                  AND julianday(si.expiry_date) - julianday('now') <= ?
                  AND julianday(si.expiry_date) - julianday('now') >= 0
                ORDER BY days_left ASC
            ''', (days,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_expired_items() -> List[dict]:
        """获取已过期食材"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT si.id, i.name as ingredient_name, si.batch_number,
                       si.quantity, si.expiry_date, si.created_at
                FROM stock_in si
                JOIN ingredients i ON si.ingredient_id = i.id
                WHERE si.expiry_date IS NOT NULL
                  AND si.expiry_date != ''
                  AND julianday(si.expiry_date) < julianday('now')
                ORDER BY si.expiry_date DESC
            ''')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
