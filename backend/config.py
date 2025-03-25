import os
from pathlib import Path
# URL白名单配置
LOGO_URL_WHITELIST = [
    "https://raw.githubusercontent.com",
    "https://cdn.jsdelivr.net",
    "https://i.imgur.com"
]

DATA_ROOT = os.path.expanduser('~') + '/.m3u-filter'
STATIC_DIR = "static"
DATA_DIR = "data"
LOGO_STATIC_DIR = "logos"
LOGO_LOGS_DIR = "logs"
DATABASE_FILE = DATA_ROOT + '/' + DATA_DIR + '/epg.db'

PATH_DATA_ROOT = Path(DATA_ROOT)
if not PATH_DATA_ROOT.exists():
    PATH_DATA_ROOT.mkdir(parents=True)

PATH_STATIC_DIR = Path(DATA_ROOT + "/" + STATIC_DIR)
if not PATH_STATIC_DIR.exists():
    PATH_STATIC_DIR.mkdir(parents=True)

PATH_DATA_DIR = Path(DATA_ROOT + "/" + DATA_DIR)
if not PATH_DATA_DIR.exists():
    PATH_DATA_DIR.mkdir(parents=True)

PATH_LOGO_STATIC_DIR = Path(DATA_ROOT + "/" + LOGO_STATIC_DIR)
if not PATH_LOGO_STATIC_DIR.exists():
    PATH_LOGO_STATIC_DIR.mkdir(parents=True)

PATH_LOGO_LOGS_DIR = Path(DATA_ROOT + "/" + LOGO_LOGS_DIR)
if not PATH_LOGO_LOGS_DIR.exists():
    PATH_LOGO_LOGS_DIR.mkdir(parents=True)

# 站点基础URL配置
BASE_URL = "http://localhost:8000"  # 开发环境默认值
STATIC_URL_PREFIX = "/static"  # 静态文件URL前缀