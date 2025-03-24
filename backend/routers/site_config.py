from fastapi import APIRouter
from config import BASE_URL, STATIC_URL_PREFIX
from models import BaseResponse

router = APIRouter()

@router.get("/site-config")
async def get_site_config():
    """获取站点配置信息"""
    return BaseResponse.success({
        "base_url": BASE_URL,
        "static_url_prefix": STATIC_URL_PREFIX
    })