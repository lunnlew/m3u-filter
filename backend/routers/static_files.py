from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import mimetypes
import logging
from urllib.parse import unquote
from config import PATH_RESOURCE_ROOT, PATH_WEB_ROOT

logger = logging.getLogger(__name__)
router = APIRouter()

# 定义直接显示而不下载的文件扩展名
DISPLAY_EXTENSIONS = {
    '.m3u': 'text/plain',
    '.m3u8': 'text/plain',
    '.txt': 'text/plain',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.html': 'text/html',
}

@router.get("/")
async def serve_web():
    return await get_web_file("index.html")

@router.get("/resource/{file_path:path}")
async def get_resource_file(file_path: str):
    """获取其他静态文件"""
    decoded_path = unquote(file_path)
    file_location = PATH_RESOURCE_ROOT / decoded_path
    
    if not file_location.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not file_location.is_file():
        raise HTTPException(status_code=400, detail="请求的不是文件")
        
    # 检查文件是否在resource目录下（防止目录遍历攻击）
    try:
        file_location.relative_to(PATH_RESOURCE_ROOT)
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")
    
    # 获取文件扩展名
    file_extension = file_location.suffix.lower()
    
    # 设置响应参数
    kwargs = {}
    
    # 如果是白名单中的扩展名，设置特定的Content-Type和Content-Disposition
    if file_extension in DISPLAY_EXTENSIONS:
        kwargs['media_type'] = DISPLAY_EXTENSIONS[file_extension]
        # Remove the incorrect parameter and let the browser handle inline display
        # based on the media_type
    else:
        # 对于其他文件类型，使用系统默认的mime类型，并设置为下载
        mime_type, _ = mimetypes.guess_type(str(file_location))
        if mime_type:
            kwargs['media_type'] = mime_type
        # Set filename parameter to trigger download
        kwargs['filename'] = file_location.name
    
    return FileResponse(file_location, **kwargs)

@router.get("/{file_path:path}")
async def get_web_file(file_path: str):
    """获取前端资源文件"""
    # Decode URL-encoded file path
    decoded_path = unquote(file_path)
    file_location = PATH_WEB_ROOT / decoded_path

    if not file_location.exists():
        raise HTTPException(status_code=404, detail="前端文件不存在")

    # 安全校验指向web子目录
    try:
        file_location.relative_to(PATH_WEB_ROOT)
    except ValueError:
        raise HTTPException(status_code=403, detail="前端资源访问被拒绝")

    return FileResponse(file_location)