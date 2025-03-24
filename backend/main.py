from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api_router
from scheduler import start_scheduler
from database import init_db

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