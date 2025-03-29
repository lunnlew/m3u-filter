import os
from pathlib import Path
# URL白名单配置
LOGO_URL_WHITELIST = [
    "https://raw.githubusercontent.com",
    "https://cdn.jsdelivr.net",
    "https://i.imgur.com"
]

# 站点基础URL配置
BASE_URL = "http://localhost:3232"  # 开发环境默认值
RESOURCE_URL_PREFIX = "/resource"  # 资源文件前缀

RESOURCE_DIR = '/resource'
LOG_DIR = '/logs'
LOGOS_DIR = '/logos'
DATA_ROOT = os.getenv('M3U_FILTER_DATA_ROOT', os.path.expanduser('~') + '/.m3u-filter')
WEB_ROOT= os.getenv('M3U_FILTER_WEB_ROOT', DATA_ROOT + '/web')
RESOURCE_ROOT= os.getenv('M3U_FILTER_RESOURCE_ROOT', DATA_ROOT + RESOURCE_DIR)
LOG_ROOT= os.getenv('M3U_FILTER_LOGS_ROOT', DATA_ROOT + LOG_DIR)
LOGOS_ROOT= os.getenv('M3U_FILTER_LOGOS_ROOT', RESOURCE_ROOT + LOGOS_DIR)
DATABASE_FILE = DATA_ROOT + '/epg.db'

PATH_DATA_ROOT = Path(DATA_ROOT)
if not PATH_DATA_ROOT.exists():
    PATH_DATA_ROOT.mkdir(parents=True)

PATH_WEB_ROOT = Path(WEB_ROOT)
if not PATH_WEB_ROOT.exists():
    PATH_WEB_ROOT.mkdir(parents=True)

PATH_RESOURCE_ROOT = Path(RESOURCE_ROOT)
if not PATH_RESOURCE_ROOT.exists():
    PATH_RESOURCE_ROOT.mkdir(parents=True)

PATH_LOG_ROOT = Path(LOG_ROOT)
if not PATH_LOG_ROOT.exists():
    PATH_LOG_ROOT.mkdir(parents=True)

PATH_LOGOS_ROOT = Path(LOGOS_ROOT)
if not PATH_LOGOS_ROOT.exists():
    PATH_LOGOS_ROOT.mkdir(parents=True)
    
# 日志配置
LOG_LEVEL = os.getenv('M3U_FILTER_LOG_LEVEL', "INFO")
LOG_FILE = LOG_ROOT + "/m3u-filter.log"