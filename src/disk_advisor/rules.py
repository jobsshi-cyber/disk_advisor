# rules.py

# ========== 永久排除：不扫描、不建议、不展示 ==========
HARD_EXCLUDE_NAMES = {
    "System32",
    "SysWOW64",
    "WinSxS",
    "Prefetch",
    "System Volume Information",
    "$Recycle.Bin",
    "Recovery",
    "Program Files",
    "Program Files (x86)",
    "ProgramData",
    "bootmgr",
    "bootnxt",
    "pagefile.sys",
    "hiberfil.sys",
    "swapfile.sys",
    "node_modules",
    ".git",  # 开发目录通常体积大但迁移/删除需开发者自行决定
}

# ========== 绿灯垃圾：可安全清理 ==========
GREEN_JUNK_PATTERNS = {
    "Temp",
    "tmp",
    "Cache",
    "cache",
    "Code Cache",
    "GPUCache",
    "thumbcache",
    "__pycache__",
    ".pytest_cache",
    "pip-cache",
    "npm-cache",
    "yarn-cache",
    "pnpm-store",
}

# 已知的绿灯具体路径（相对用户目录或系统目录）
GREEN_KNOWN_PATHS = [
    ("用户临时文件", r"%LOCALAPPDATA%\Temp"),
    ("系统临时文件", r"C:\Windows\Temp"),
    ("Windows 更新缓存", r"C:\Windows\SoftwareDistribution\Download"),
    ("Chrome 缓存", r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"),
    ("Edge 缓存", r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache"),
    ("缩略图缓存", r"%LOCALAPPDATA%\Microsoft\Windows\Explorer"),
]

# ========== 黄灯：需用户自行确认 ==========
YELLOW_NAMES = {
    "Downloads",
    "Desktop",
    "Documents",
    "WeChat Files",
    "Tencent Files",
    "QQ Files",
    "Backup",
    "backup",
}

# ========== 迁移策略表 ==========
# 只对“可安全迁移”的类型给出建议；不在此表中的大文件只报告位置，不给迁移建议
MIGRATION_STRATEGY = {
    ".mp4": "个人媒体文件，可直接剪切到其他盘",
    ".mkv": "个人媒体文件，可直接剪切到其他盘",
    ".avi": "个人媒体文件，可直接剪切到其他盘",
    ".mov": "个人媒体文件，可直接剪切到其他盘",
    ".iso": "归档镜像，可直接剪切到其他盘",
    ".zip": "归档压缩包，可直接剪切到其他盘",
    ".rar": "归档压缩包，可直接剪切到其他盘",
    ".7z": "归档压缩包，可直接剪切到其他盘",
    ".vmdk": "虚拟机磁盘，剪切后在虚拟机软件中重新指定路径",
    ".vhdx": "虚拟机磁盘，剪切后在虚拟机软件中重新指定路径",
}
