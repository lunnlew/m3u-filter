from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database import get_db_connection
from models import BaseResponse
import logging
logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/epg-programs")
async def get_epg_programs(
    channel_id: Optional[str] = None,
    channel_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
):
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # 计算分页偏移量
        offset = (page - 1) * page_size
        
        # 构建基础查询，使用INDEXED BY提示优化查询
        base_query = """
            FROM epg_programs p INDEXED BY idx_epg_programs_channel
            INNER JOIN epg_channels c INDEXED BY idx_epg_channels_name ON p.channel_id = c.channel_id AND p.source_id = c.source_id
            INNER JOIN epg_sources s ON p.source_id = s.id 
            WHERE 1=1
        """
        params = []
        
        if channel_id:
            base_query += " AND p.channel_id = ?"
            params.append(channel_id)
        if channel_name:
            base_query += " AND c.display_name LIKE ?"
            params.append(f"%{channel_name}%")
        if start_time:
            base_query += " AND p.start_time >= ?"
            params.append(start_time)
        if end_time:
            base_query += " AND p.end_time <= ?"
            params.append(end_time)
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) {base_query}"
        c.execute(count_query, params)
        total = c.fetchone()[0]
        
        # 获取分页数据
        data_query = f"SELECT p.*, c.display_name as channel_name, s.name as source_name {base_query} LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        c.execute(data_query, params)
        columns = [description[0] for description in c.description]
        programs = [dict(zip(columns, row)) for row in c.fetchall()]
        
        return BaseResponse.success(data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": programs
        })