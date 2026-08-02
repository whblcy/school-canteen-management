# -*- mode: python ; coding: utf-8 -*-
# V2 打包配置（对应 main_v2.py + school_canteen 包）
# 与 V1 的 .spec 平行，产物名为「学校食堂食材管理系统V2」，
# 数据库默认写到 canteen_v2.db（见 school_canteen/config.py），与 V1 物理隔离。

a = Analysis(
    ['main_v2.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app_icon.ico', '.'),
        ('表格', '表格'),
        ('食材导入模板.xlsx', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='学校食堂食材管理系统V2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='学校食堂食材管理系统V2',
)
