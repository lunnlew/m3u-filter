import os
from typing import Optional
import aiohttp
import aiofiles
import uuid
import re
from urllib.parse import urlparse
from config import LOGO_URL_WHITELIST, STATIC_DIR, LOGO_STATIC_DIR
from database import get_db_connection

def is_url_in_whitelist(url: str) -> bool:
    """检查URL是否在白名单中或是相对路径"""
    # 如果是相对路径（不以http://或https://开头），直接返回True
    if not url.startswith('http://') and not url.startswith('https://'):
        return True
    
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return any(base_url.startswith(allowed_url) for allowed_url in LOGO_URL_WHITELIST)

def sanitize_filename(filename: str) -> str:
    """处理文件名，移除非法字符"""
    # 移除非法字符，只保留字母、数字、下划线和连字符
    filename = re.sub(r'[^\w\-]', '_', filename)
    # 确保文件名不为空
    return filename or 'logo'

async def download_and_save_logo(logo_url: str, channel_name: Optional[str] = None) -> str:
    """下载logo并保存到静态文件目录
    
    Args:
        logo_url: Logo的URL地址
        channel_name: 频道名称，用作文件名的基础
        
    Returns:
        str: 保存后的相对路径
    """
    # 确保目录存在
    logo_dir = os.path.join(STATIC_DIR, LOGO_STATIC_DIR)
    os.makedirs(logo_dir, exist_ok=True)
    
    # 获取文件扩展名
    parsed_url = urlparse(logo_url)
    _, ext = os.path.splitext(os.path.basename(parsed_url.path))
    if not ext:
        ext = '.png'  # 默认扩展名
    
    # 生成基础文件名
    base_filename = sanitize_filename(channel_name) if channel_name else 'logo'
    filename = f"{base_filename}{ext}"
    
    # 获取代理配置
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM proxy_config LIMIT 1")
        columns = [description[0] for description in c.description]
        proxy_config_row = c.fetchone()
    
    proxy_config = None
    if proxy_config_row:
        proxy_config = dict(zip(columns, proxy_config_row))
    
    # 设置代理
    session_kwargs = {}
    if proxy_config and proxy_config.get('enabled'):
        proxy_type = proxy_config.get('proxy_type', 'http')
        host = proxy_config.get('host')
        port = proxy_config.get('port')
        username = proxy_config.get('username')
        password = proxy_config.get('password')
        
        if host and port:
            proxy_url = f"{proxy_type}://"
            if username and password:
                proxy_url += f"{username}:{password}@"
            proxy_url += f"{host}:{port}"
            session_kwargs['proxy'] = proxy_url
    
    # 下载文件
    async with aiohttp.ClientSession(**session_kwargs) as session:
        async with session.get(logo_url) as response:
            if response.status == 200:
                content = await response.read()
                
                # 检查是否存在同名文件
                save_path = os.path.join(logo_dir, filename)
                relative_path = f"/{LOGO_STATIC_DIR}/{filename}"
                
                if os.path.exists(save_path):
                    # 比较文件大小
                    existing_size = os.path.getsize(save_path)
                    new_size = len(content)
                    
                    if existing_size == new_size:
                        # 文件大小相同，直接返回已存在文件的路径
                        return relative_path
                    else:
                        # 使用logo_url生成固定的子目录名
                        import hashlib
                        # 使用logo_url的MD5哈希值前8位作为子目录名
                        unique_id = hashlib.md5(logo_url.encode()).hexdigest()[:8]
                        sub_dir = os.path.join(logo_dir, unique_id)
                        os.makedirs(sub_dir, exist_ok=True)
                        save_path = os.path.join(sub_dir, filename)
                        relative_path = f"/{LOGO_STATIC_DIR}/{unique_id}/{filename}"
                
                # 保存文件
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(content)
                    return relative_path
            else:
                raise Exception(f"下载logo失败: {response.status}")