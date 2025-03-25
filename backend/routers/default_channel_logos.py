from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel, HttpUrl
from database import get_db_connection
import sqlite3
from utils import is_url_in_whitelist, download_and_save_logo
from models import BaseResponse
import logging
logger = logging.getLogger(__name__)
router = APIRouter()

class ChannelLogoBase(BaseModel):
    channel_name: str
    logo_url: str
    priority: int = 0

class ChannelLogo(ChannelLogoBase):
    id: int

@router.get("/default-channel-logos")
async def get_channel_logos():
    """获取所有默认频道台标配置"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, channel_name, logo_url, priority FROM default_channel_logos ORDER BY priority DESC, channel_name"
        )
        logos = cursor.fetchall()
        return BaseResponse.success(data=[
            ChannelLogo(
                id=row[0],
                channel_name=row[1],
                logo_url=row[2],
                priority=row[3]
            ) for row in logos
        ])

@router.post("/default-channel-logos")
async def create_channel_logo(logo: ChannelLogoBase):
    """添加新的频道台标配置"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # 检查logo URL是否在白名单中
            logo_url = str(logo.logo_url)
            if not is_url_in_whitelist(logo_url):
                # 下载并保存logo
                logo_url = await download_and_save_logo(logo_url, logo.channel_name)
            
            cursor.execute(
                "INSERT INTO default_channel_logos (channel_name, logo_url, priority) VALUES (?, ?, ?)",
                (logo.channel_name, logo_url, logo.priority)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return BaseResponse.success(data=ChannelLogo(
                id=new_id,
                channel_name=logo.channel_name,
                logo_url=logo.logo_url,
                priority=logo.priority
            ))
        except sqlite3.IntegrityError:
            return BaseResponse.error(message="频道名称已存在", code=400)

@router.put("/default-channel-logos/{logo_id}")
async def update_channel_logo(logo_id: int, logo: ChannelLogoBase):
    """更新频道台标配置"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # 检查logo URL是否在白名单中
            logo_url = str(logo.logo_url)
            if not is_url_in_whitelist(logo_url):
                # 下载并保存logo
                logo_url = await download_and_save_logo(logo_url, logo.channel_name)
            
            cursor.execute(
                "UPDATE default_channel_logos SET channel_name = ?, logo_url = ?, priority = ? WHERE id = ?",
                (logo.channel_name, logo_url, logo.priority, logo_id)
            )
            if cursor.rowcount == 0:
                return BaseResponse.error(message="未找到指定的台标配置", code=404)
            conn.commit()
            return BaseResponse.success(data=ChannelLogo(
                id=logo_id,
                channel_name=logo.channel_name,
                logo_url=logo.logo_url,
                priority=logo.priority
            ))
        except sqlite3.IntegrityError:
            return BaseResponse.error(message="频道名称已存在", code=400)

@router.delete("/default-channel-logos/{logo_id}")
async def delete_channel_logo(logo_id: int):
    """删除频道台标配置"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM default_channel_logos WHERE id = ?", (logo_id,))
        if cursor.rowcount == 0:
            return BaseResponse.error(message="未找到指定的台标配置", code=404)
        conn.commit()
        return BaseResponse.success(message="台标配置已删除")