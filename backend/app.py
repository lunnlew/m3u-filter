from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api_router
from scheduler import start_scheduler
from database import init_db
from config import PATH_LOG_ROOT, LOG_FILE, LOG_LEVEL
import logging
import logging.handlers
import os

# 配置日志
def setup_logger():
    if not os.path.exists(PATH_LOG_ROOT):
        os.makedirs(PATH_LOG_ROOT)
    
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 文件处理器（按天轮转）
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=PATH_LOG_ROOT / LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# 设置日志
setup_logger()
logger = logging.getLogger(__name__)

def create_app():

    app = FastAPI()

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router)

    # 初始化数据库
    init_db()

    # 启动调度器
    start_scheduler()
    
    return app