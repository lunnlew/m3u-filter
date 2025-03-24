from fastapi import APIRouter, HTTPException
from typing import List
import sqlite3
from datetime import datetime
from models import StreamSource
from sync import sync_stream_source
from database import get_db_connection
from scheduler import update_stream_schedule
from models import BaseResponse

router = APIRouter()

@router.get("/stream-sources")
async def get_stream_sources():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM stream_sources")
        columns = [description[0] for description in c.description]
        sources = [dict(zip(columns, row)) for row in c.fetchall()]
        return BaseResponse.success(data=sources)

@router.post("/stream-sources")
async def create_stream_source(source: StreamSource):
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO stream_sources (name, url, type, active, sync_interval, x_tvg_url, catchup, catchup_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (source.name, source.url, source.type, source.active, source.sync_interval, source.x_tvg_url, source.catchup, source.catchup_source)
            )
            source_id = c.lastrowid
            conn.commit()
            source.id = source_id
            # 更新同步计划
            update_stream_schedule(source_id)
            return BaseResponse.success(data=source)
        except sqlite3.IntegrityError:
            return BaseResponse.error(message="URL已存在", code=400)

@router.put("/stream-sources/{source_id}")
async def update_stream_source(source_id: int, source: StreamSource):
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "UPDATE stream_sources SET name = ?, url = ?, type = ?, active = ?, sync_interval = ?, x_tvg_url = ?, catchup = ?, catchup_source = ? WHERE id = ?",
                (source.name, source.url, source.type, source.active, source.sync_interval, source.x_tvg_url, source.catchup, source.catchup_source, source_id)
            )
            if c.rowcount == 0:
                return BaseResponse.error(message="直播源不存在", code=404)
            conn.commit()
            source.id = source_id
            # 更新同步计划
            update_stream_schedule(source_id)
            return BaseResponse.success(data=source)
        except sqlite3.IntegrityError:
            return BaseResponse.error(message="URL已存在", code=400)

@router.delete("/stream-sources/{source_id}")
async def delete_stream_source(source_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM stream_sources WHERE id = ?", (source_id,))
        if c.rowcount == 0:
            return BaseResponse.error(message="直播源不存在", code=404)
        conn.commit()
        return BaseResponse.success(message="直播源已删除")

@router.post("/stream-sources/{source_id}/sync")
async def sync_single_stream_source(source_id: int):
    try:
        # 异步执行同步任务，不等待完成
        import asyncio
        asyncio.create_task(sync_stream_source(source_id))
        return BaseResponse.success(message="同步任务已启动")
    except Exception as e:
        return BaseResponse.error(message=f"启动同步任务时发生错误: {str(e)}", code=500)