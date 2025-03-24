from fastapi import APIRouter, HTTPException
from typing import List
import sqlite3
from datetime import datetime
from models import EPGSource
from models import BaseResponse
from sync import sync_epg_source, sync_all_active_sources
from scheduler import update_source_schedule, get_source_next_run
from database import get_db_connection

router = APIRouter()

@router.get("/epg-sources")
async def get_epg_sources():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM epg_sources")
        columns = [description[0] for description in c.description]
        sources = [dict(zip(columns, row)) for row in c.fetchall()]
        return BaseResponse.success(data=sources)

@router.post("/epg-sources")
async def create_epg_source(source: EPGSource):
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO epg_sources (name, url, active, sync_interval, default_language) VALUES (?, ?, ?, ?, ?)",
                (source.name, source.url, source.active, source.sync_interval, source.default_language)
            )
            source_id = c.lastrowid
            conn.commit()
            source.id = source_id
            
            # 添加同步计划
            assert source_id is not None, "Failed to get source_id after insert"
            update_source_schedule(source_id)
            return BaseResponse.success(data=source)
        except sqlite3.IntegrityError:
            return BaseResponse.error(message="URL已存在", code=400)

@router.put("/epg-sources/{source_id}")
async def update_epg_source(source_id: int, source: EPGSource):
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "UPDATE epg_sources SET name = ?, url = ?, active = ?, sync_interval = ?, default_language = ? WHERE id = ?",
                (source.name, source.url, source.active, source.sync_interval, source.default_language, source_id)
            )
            if c.rowcount == 0:
                return BaseResponse.error(message="EPG源不存在", code=404)
            conn.commit()
            source.id = source_id
            
            # 更新同步计划
            update_source_schedule(source_id)
            return BaseResponse.success(data=source)
        except sqlite3.IntegrityError:
            return BaseResponse.error(message="URL已存在", code=400)

@router.delete("/epg-sources/{source_id}")
async def delete_epg_source(source_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM epg_sources WHERE id = ?", (source_id,))
        if c.rowcount == 0:
            return BaseResponse.error(message="EPG源不存在", code=404)
        conn.commit()
        return BaseResponse.success(message="EPG源已删除")

@router.post("/epg-sources/{source_id}/sync")
async def sync_single_epg_source(source_id: int):
    try:
        # 在后台异步执行同步操作
        import asyncio
        asyncio.create_task(sync_epg_source(source_id))
        return BaseResponse.success(message="EPG源同步已开始")
    except ValueError as ve:
        return BaseResponse.error(message=str(ve), code=404)
    except Exception as e:
        return BaseResponse.error(message=f"启动EPG数据同步时发生错误: {str(e)}", code=500)

@router.post("/epg-sources/sync-all")
async def sync_all_sources():
    try:
        # 在后台异步执行同步操作
        import asyncio
        asyncio.create_task(sync_all_active_sources())
        return BaseResponse.success(message="所有EPG源同步已开始")
    except Exception as e:
        return BaseResponse.error(message=f"启动EPG数据同步时发生错误: {str(e)}", code=500)

@router.get("/epg-sources/{source_id}/next-sync")
async def get_next_sync_time(source_id: int):
    next_run = get_source_next_run(source_id)
    if next_run:
        return BaseResponse.success(data={"next_sync": next_run})
    return BaseResponse.error(message="未找到该数据源的同步计划", code=404)