"""
集中配置管理 - 所有可变参数、路径、常量的统一入口
替代散落在各模块的硬编码值
"""
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _resource_root() -> Path:
    """资源根目录（只读）：打包后指向 PyInstaller 解包目录，开发时指向项目根"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _data_root() -> Path:
    """可写数据根目录：打包后放在 exe 同目录（持久、可写），开发时指向项目根。
    注意：不能用 sys._MEIPASS，那是临时只读解包目录，写入会失败。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


APP_ROOT = _resource_root()
DATA_ROOT = _data_root()
APP_NAME = "学校食堂食材管理系统"
APP_VERSION = "v2.0.0"


@dataclass(frozen=True)
class Paths:
    """路径配置（不可变，防止运行时被篡改）"""
    root: Path = APP_ROOT
    db_file: Path = DATA_ROOT / os.environ.get("CANTEEN_DB_OVERRIDE", "canteen_v2.db")
    log_dir: Path = DATA_ROOT / "logs"
    icon_file: Path = APP_ROOT / "app_icon.ico"
    template_dir: Path = APP_ROOT / "表格"
    import_template: Path = APP_ROOT / "食材导入模板.xlsx"

    def resource(self, relative: str) -> Path:
        """获取资源文件路径"""
        return self.root / relative

    def template(self, filename: str) -> Path:
        """获取报表模板路径"""
        return self.template_dir / filename

    def ensure_dirs(self):
        """确保必要目录存在"""
        self.log_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Security:
    """安全配置"""
    pbkdf2_iterations: int = 100_000
    salt_length: int = 16  # bytes -> hex 32 chars
    hash_algorithm: str = "sha256"


@dataclass(frozen=True)
class UI:
    """UI 配置常量"""
    window_min_width: int = 1200
    window_min_height: int = 800
    nav_width: int = 220
    base_dialog_width: int = 500
    form_field_min_width: int = 250
    button_min_width: int = 80
    button_spacing: int = 8
    operation_spacing: int = 10

    # macOS 风格配色
    color_blue: str = "#0066cc"
    color_blue_hover: str = "#0077ed"
    color_green: str = "#34c759"
    color_red: str = "#ff3b30"
    color_orange: str = "#ff9500"
    color_gray: str = "#86868b"
    color_light_gray: str = "#f5f5f7"
    color_bg: str = "#f5f5f7"
    color_border: str = "#d2d2d7"
    color_text: str = "#1d1d1f"
    color_text_secondary: str = "#6e6e73"
    color_white: str = "#ffffff"


@dataclass(frozen=True)
class Business:
    """业务规则常量"""
    expiry_warning_days: int = 7
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    default_admin_real_name: str = "系统管理员"
    confirm_delete_phrase: str = "确认删除"
    default_inspectors: tuple = ("张三", "李四", "王五", "赵六")
    default_categories: tuple = (
        ("蔬菜类", "各类新鲜蔬菜"),
        ("肉类", "猪肉、牛肉、鸡肉等"),
        ("水产类", "鱼、虾、蟹等"),
        ("豆制品", "豆腐、豆皮等"),
        ("粮油类", "米、面、油等"),
        ("调味品", "盐、糖、酱油等"),
        ("蛋类", "鸡蛋、鸭蛋等"),
        ("水果类", "各类水果"),
    )


@dataclass
class AppConfig:
    """全局配置聚合"""
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    paths: Paths = field(default_factory=Paths)
    security: Security = field(default_factory=Security)
    ui: UI = field(default_factory=UI)
    business: Business = field(default_factory=Business)

    @classmethod
    def load(cls) -> "AppConfig":
        """加载配置（未来可扩展为从文件/env读取）"""
        cfg = cls()
        cfg.paths.ensure_dirs()
        return cfg


# 全局单例配置
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """获取全局配置单例"""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config
