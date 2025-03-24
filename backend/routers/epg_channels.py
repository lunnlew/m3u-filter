from fastapi import APIRouter, HTTPException
from typing import List
from models import EPGChannel
from models import BaseResponse
from database import get_db_connection
from fastapi.responses import FileResponse
from datetime import datetime
import xml.etree.ElementTree as ET
import os
from config import BASE_URL, STATIC_URL_PREFIX

from pathlib import Path

router = APIRouter()

# 配置静态文件目录路径
STATIC_DIR = Path("data")

@router.get("/epg-channels")
async def get_channels():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT 
                epg_channels.id, 
                epg_channels.channel_id, 
                epg_channels.display_name, 
                epg_channels.language, 
                epg_channels.category, 
                COALESCE(
                    epg_channels.local_logo_path,
                    epg_channels.logo_url,
                    (SELECT local_logo_path FROM default_channel_logos 
                    WHERE channel_name = epg_channels.display_name 
                    ORDER BY priority DESC LIMIT 1),
                    (SELECT logo_url FROM default_channel_logos 
                    WHERE channel_name = epg_channels.display_name 
                    ORDER BY priority DESC LIMIT 1)
                ) as logo_url, 
                epg_sources.name AS source_name 
            FROM epg_channels 
            LEFT JOIN epg_sources ON epg_channels.source_id = epg_sources.id
        """)
        columns = [description[0] for description in c.description]
        channels = [dict(zip(columns, row)) for row in c.fetchall()]
        return BaseResponse.success(data=channels)

@router.post("/epg-channels")
async def create_channel(channel: EPGChannel):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO epg_channels (display_name, language, category, logo_url, local_logo_path) VALUES (?, ?, ?, ?, ?)",
            (channel.display_name, channel.language, channel.category, channel.logo_url, channel.local_logo_path)
        )
        channel_id = c.lastrowid
        conn.commit()
        channel.id = channel_id
        return BaseResponse.success(data=channel)

@router.put("/epg-channels/{channel_id}")
async def update_channel(channel_id: int, channel: EPGChannel):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE epg_channels SET display_name = ?, language = ?, category = ?, logo_url = ?, local_logo_path = ? WHERE id = ?",
            (channel.display_name, channel.language, channel.category, channel.logo_url, channel.local_logo_path, channel_id)
        )
        if c.rowcount == 0:
            return BaseResponse.error(message="频道不存在", code=404)
        conn.commit()
        channel.id = channel_id
        return BaseResponse.success(data=channel)

@router.delete("/epg-channels/{channel_id}")
async def delete_channel(channel_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM epg_channels WHERE id = ?", (channel_id,))
        if c.rowcount == 0:
            return BaseResponse.error(message="频道不存在", code=404)
        conn.commit()
        return BaseResponse.success(message="频道已删除")

@router.delete("/epg-channels-clear-all")
async def clear_all_channels():
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("BEGIN TRANSACTION")
            # 首先清空节目表，因为它依赖于频道表
            c.execute("DELETE FROM epg_programs")
            # 然后清空频道表
            c.execute("DELETE FROM epg_channels")
            conn.commit()
            return BaseResponse.success(message="所有频道和节目数据已清空")
        except Exception as e:
            conn.rollback()
            return BaseResponse.error(message=str(e), code=500)

@router.delete("/epg-programs-clear-all")
async def clear_all_programs():
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("DELETE FROM epg_programs")
            conn.commit()
            return BaseResponse.success(message="所有节目数据已清空")
        except Exception as e:
            conn.rollback()
            return BaseResponse.error(message=str(e), code=500)

@router.post("/epg-channels/export-xml")
async def export_epg_xml():
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # 创建XML根元素
        tv = ET.Element("tv")
        tv.set("generator-info-name", "M3U Filter EPG Generator")
        tv.set("generator-info-url", "https://github.com/your-repo/m3u-filter")
        
        # 获取启用的频道信息，使用与get_channels相同的logo获取逻辑，并添加去重逻辑
        c.execute("""
            SELECT
                epg_channels.id, 
                epg_channels.channel_id, 
                epg_channels.display_name, 
                epg_channels.language, 
                epg_channels.category,
                COALESCE(
                    epg_channels.local_logo_path,
                    epg_channels.logo_url,
                    (SELECT local_logo_path FROM default_channel_logos 
                    WHERE channel_name = epg_channels.display_name 
                    ORDER BY priority DESC LIMIT 1),
                    (SELECT logo_url FROM default_channel_logos 
                    WHERE channel_name = epg_channels.display_name 
                    ORDER BY priority DESC LIMIT 1)
                ) as logo_url
            FROM epg_channels 
        """)
        columns = [description[0] for description in c.description]
        channels = [dict(zip(columns, row)) for row in c.fetchall()]
        
        channels_names_map = {}
        channels_names_id_map = {}

        # 添加频道信息到XML
        for channel in channels:
            channels_names_map[str(channel['channel_id'] or channel['id'])] = channel['display_name']
            if channel['display_name'] in channels_names_id_map:
                continue

            channel_elem = ET.SubElement(tv, "channel")
            channel_elem.set("id", str(channel['channel_id'] or channel['id']))
            
            display_name = ET.SubElement(channel_elem, "display-name")
            display_name.set("lang", channel['language'] or "en")
            display_name.text = channel['display_name']
            
            if channel['logo_url']:
                icon = ET.SubElement(channel_elem, "icon")
                icon.set("src", BASE_URL + STATIC_URL_PREFIX + channel['logo_url'])
            
            if channel['category']:
                category = ET.SubElement(channel_elem, "category")
                category.set("lang", channel['language'] or "en")
                category.text = channel['category']
                
            channels_names_id_map[channel['display_name']] = str(channel['channel_id'] or channel['id'])
        
        # 获取频道的节目信息
        channel_ids = [str(ch['id']) for ch in channels]
        if channel_ids:
            c.execute("""
                SELECT 
                    channel_id,
                    title,
                    start_time,
                    end_time,
                    description
                FROM epg_programs
                WHERE channel_id IN ({}) 
                ORDER BY start_time
            """.format(','.join('?' * len(channel_ids))), channel_ids)
            columns = [description[0] for description in c.description]
            programs = [dict(zip(columns, row)) for row in c.fetchall()]
            
            programs_names_map = {}
            # 添加节目信息到XML
            for program in programs:
                if program['title']+program['start_time'] in programs_names_map:
                    continue
                programme = ET.SubElement(tv, "programme")
                programme.set("start", program['start_time'])
                programme.set("stop", program['end_time'])

                programme.set("channel", channels_names_id_map[channels_names_map[str(program['channel_id'])]])
                
                title = ET.SubElement(programme, "title")
                title.set("lang", "en")
                title.text = program['title']
                
                if program['description']:
                    desc = ET.SubElement(programme, "desc")
                    desc.set("lang", "en")
                    desc.text = program['description']

                programs_names_map[program['title']+program['start_time']] = True
        
        # 生成XML文件
        xml_str = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
        # 保存到m3u文件夹
        m3u_dir = STATIC_DIR / 'm3u'
        # 确保静态文件目录存在
        if not m3u_dir.exists():
            m3u_dir.mkdir(parents=True)
        
        filename = "epg.xml"
        file_path = m3u_dir / filename

        with open(file_path, "wb") as f:
            f.write(xml_str)
    
    return BaseResponse.success({"url_path": f"/m3u/{filename}"})