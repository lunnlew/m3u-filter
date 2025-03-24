from fastapi import APIRouter, HTTPException
import sqlite3
from models import ProxyConfig
from database import get_db_connection
from models import BaseResponse

router = APIRouter()

@router.get("/proxy-config")
async def get_proxy_config():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM proxy_config LIMIT 1")
        columns = [description[0] for description in c.description]
        proxy_config_row = c.fetchone()
    
    if not proxy_config_row:
        return BaseResponse.success(data=ProxyConfig())
    
    return BaseResponse.success(data=ProxyConfig(**dict(zip(columns, proxy_config_row))))

@router.put("/proxy-config")
async def update_proxy_config(config: ProxyConfig):
    with get_db_connection() as conn:
        c = conn.cursor()
        
        try:
            c.execute(
                "UPDATE proxy_config SET enabled = ?, proxy_type = ?, host = ?, port = ?, username = ?, password = ? WHERE id = 1",
                (config.enabled, config.proxy_type, config.host, config.port, config.username, config.password)
            )
            
            if c.rowcount == 0:
                c.execute(
                    "INSERT INTO proxy_config (enabled, proxy_type, host, port, username, password) VALUES (?, ?, ?, ?, ?, ?)",
                    (config.enabled, config.proxy_type, config.host, config.port, config.username, config.password)
                )
            
            conn.commit()
            return BaseResponse.success(data=config)
        except Exception as e:
            conn.rollback()
            return BaseResponse.error(message=f"更新代理配置时发生错误: {str(e)}", code=500)