import logging
from app import create_app  # 使用相对导入
from scheduler import start_scheduler  # 导入调度器启动函数

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    import sys
    # 检查是否已经运行了 uvicorn
    if "uvicorn" not in " ".join(sys.argv):
        # 启动调度器
        start_scheduler()
        
        uvicorn.run(
            "app:create_app",  # 修改为当前模块
            host="0.0.0.0",
            port=3232,
            loop="asyncio",
            reload=False,
            workers=1,
            log_config=None,
            factory=True
        )