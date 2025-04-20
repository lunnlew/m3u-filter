from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Tuple
import sqlite3
from datetime import datetime
import asyncio
from models import StreamTrack
from database import get_db_connection
from typing import Dict
from models import BaseResponse
from utils import *
from modules.stream_tracks.utils.util import *

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stream-tracks")
async def get_stream_tracks(
    name: Optional[str] = None,
    group_title: Optional[str] = None,
    source_id: Optional[int] = None,
    test_status: Optional[bool] = None,
    page: int = 1,
    page_size: int = 10,
):
    with get_db_connection() as conn:
        c = conn.cursor()
        # 构建基础查询条件
        where_clause = "WHERE 1=1"
        params = []

        if group_title:
            where_clause += " AND st.group_title = ?"
            params.append(group_title)
        if name:
            where_clause += " AND st.name LIKE ?"
            params.append(f"%{name}%")
        if source_id:
            where_clause += " AND st.source_id = ?"
            params.append(source_id)
        if test_status is not None:
            where_clause += " AND st.test_status =?"
            params.append(test_status == True)

        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM stream_tracks st {where_clause}"
        c.execute(count_query, params)
        total = c.fetchone()[0]

        # 计算分页参数
        offset = (page - 1) * page_size
        # 获取分页数据，包含source信息
        query = f"""SELECT st.*, ss.name as source_name, ss.url as source_url, ss.type as source_type, 
                 COALESCE(st.download_speed, 0) as download_speed,
                 COALESCE(st.probe_failure_count, 0) as probe_failure_count,
                 st.last_failure_time
                 FROM stream_tracks st 
                 LEFT JOIN stream_sources ss ON st.source_id = ss.id 
                 {where_clause} 
                 LIMIT ? OFFSET ?"""

        params.extend([page_size, offset])

        c.execute(query, params)
        columns = [description[0] for description in c.description]
        tracks = [dict(zip(columns, row)) for row in c.fetchall()]
        
        return BaseResponse.success(data={
            "items": tracks,
            "total": total,
            "page": page,
            "page_size": page_size
        })

@router.get("/stream-tracks/{track_id}")
async def get_stream_track(track_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM stream_tracks WHERE id = ?", (track_id,))
        track = c.fetchone()
        if not track:
            return BaseResponse.error(message="直播源不存在", code=404)
        columns = [description[0] for description in c.description]
        return BaseResponse.success(data=dict(zip(columns, track)))

@router.put("/stream-tracks/{track_id}")
async def update_stream_track(track_id: int, track: StreamTrack):
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "UPDATE stream_tracks SET name = ?, url = ?, group_title = ? WHERE id = ?",
                (track.name, track.url, track.group_title, track_id)
            )
            if c.rowcount == 0:
                return BaseResponse.error(message="直播源不存在", code=404)
            conn.commit()
            logger.info(f"频道已更新: {track_id}, 名称: {track.name}")
            track.id = track_id
            return BaseResponse.success(data=track)
        except sqlite3.IntegrityError:
            return BaseResponse.error(message="直播源URL已存在", code=400)

@router.post("/stream-tracks/{track_id}/test")
async def test_single_track(track_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(test_stream_track, track_id)
    return BaseResponse.success(message="测试任务已启动")

@router.post("/stream-tracks/test-all")
async def test_all_tracks():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id FROM stream_tracks 
            WHERE COALESCE(probe_failure_count, 0) < 5
            AND (last_test_time IS NULL OR 
                 datetime(last_test_time) < datetime('now', '-1 hour'))
        """)
        track_ids = [row[0] for row in c.fetchall()]
        
        # 创建任务记录
        c.execute("""
            INSERT INTO stream_tasks (
                task_type, status, total_items
            ) VALUES (?, ?, ?)
        """, ('batch_test', 'pending', len(track_ids)))
        task_id = c.lastrowid
        conn.commit()
        
        # 启动后台处理任务
        asyncio.create_task(process_batch_tasks(task_id, track_ids))
        
        return BaseResponse.success(
            data={"task_id": task_id},
            message=f"批量测试任务已创建，任务ID: {task_id}"
        )

async def process_batch_tasks(task_id: int, track_ids: List[int]):
    """处理批量测试任务"""
    BATCH_SIZE = 50
    MAX_CONCURRENT = 10
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    # 初始化任务状态
    task_state = {
        'total': len(track_ids),
        'processed': 0,
        'success': 0,
        'failed': 0,
        'results': [],
        'errors': []
    }

    async def process_batch(batch_ids: List[int]):
        """处理单个批次"""
        tasks = [test_single_track(track_id, semaphore) for track_id in batch_ids]
        batch_results = await asyncio.gather(*tasks)
        
        for result in batch_results:
            task_state['processed'] += 1
            
            if result['status']:
                task_state['success'] += 1
                task_state['results'].append(result)
            else:
                task_state['failed'] += 1
                if result['error'] != '频道不存在':
                    task_state['results'].append(result)
                task_state['errors'].append({
                    'track_id': result['track_id'],
                    'error': result['error']
                })
        
        # 更新任务进度
        update_task_progress(
            task_id, 
            task_state['processed'], 
            task_state['total'], 
            task_state['results']
        )
        logger.info(
            f"任务进度: {task_state['processed']}/{task_state['total']} "
            f"(成功: {task_state['success']}, 失败: {task_state['failed']})"
        )
        await asyncio.sleep(0.5)  # 批次间延迟

    try:
        # 分批处理所有ID
        for i in range(0, len(track_ids), BATCH_SIZE):
            batch = track_ids[i:i + BATCH_SIZE]
            await process_batch(batch)

        # 最终任务状态
        final_results = {
            'results': {str(r['track_id']): r for r in task_state['results']},
            'statistics': {
                'total': task_state['total'],
                'processed': task_state['processed'],
                'success': task_state['success'],
                'failed': task_state['failed']
            },
            'errors': task_state['errors']
        }

        if task_state['failed'] == task_state['total']:
            mark_task_failed(task_id, "所有频道测试失败")
        else:
            mark_task_completed(task_id, final_results)

    except Exception as e:
        logger.debug(f"批量测试任务 {task_id} 执行失败: {str(e)}")
        mark_task_failed(task_id, str(e))
        raise

async def test_single_track(track_id: int, semaphore: asyncio.Semaphore):
    """测试单个频道(提取为模块级函数)"""
    async with semaphore:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM stream_tracks WHERE id = ?", (track_id,))
                result = cursor.fetchone()
                if not result:
                    return {
                        'track_id': track_id,
                        'status': False,
                        'error': '频道不存在'
                    }
                url = result[0]

            status, latency, stream_info = await test_stream_url(url, track_id)
            update_track_result(track_id, status, latency, stream_info)
            
            await update_stream_status(
                track_id=track_id,
                url=url,
                success=status == True,
                test_time=datetime.now()
            )

            return {
                'track_id': track_id,
                'status': status,
                'latency': latency,
                'error': None if status else '测试未通过',
                **stream_info
            }
        except Exception as e:
            error_msg = str(e)
            logger.debug(f"处理频道 {track_id} 时出错: {error_msg}")
            await update_stream_status(
                track_id=track_id,
                url=url,
                success=False,
                test_time=datetime.now()
            )
            return {
                'track_id': track_id,
                'status': False,
                'error': error_msg
            }

def sync_test_stream_url(url: str, track_id: int) -> tuple[bool, float, dict]:
    # 将异步的test_stream_url转换为同步版本
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_stream_url(url, track_id))
    finally:
        loop.close()


@router.get("/stream-tasks/{task_id}")
async def get_stream_task(task_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, task_type, status, progress, total_items, processed_items,
                   created_at, updated_at, result 
            FROM stream_tasks 
            WHERE id = ?
        """, (task_id,))
        task = c.fetchone()
        if not task:
            return BaseResponse.error(message="任务不存在", code=404)
        
        columns = [description[0] for description in c.description]
        return BaseResponse.success(data=dict(zip(columns, task)))

@router.delete("/stream-tracks/{track_id}")
async def delete_stream_track(track_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM stream_tracks WHERE id = ?", (track_id,))
        if c.rowcount == 0:
            return BaseResponse.error(message="直播源不存在", code=404)
        conn.commit()
        logger.info(f"频道已删除: {track_id}")
        return BaseResponse.success(message="频道已删除")


# 添加失败计数器相关的常量和缓存
FAILURE_THRESHOLD = 4  # 允许的最大失败次数
FAILURE_WINDOW = 300  # 失败记录的有效期（秒）
FAILURE_DECAY_TIME = 1800  # 失败次数衰减时间（秒）

# 域名失败计数缓存
domain_failures: Dict[str, List[Tuple[datetime, str]]] = {}


@router.get("/stream-tracks/statistics")
async def get_stream_statistics():
    """获取流媒体测试统计信息"""
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            # 获取总体统计
            c.execute("""
                SELECT 
                    COUNT(*) as total_tracks,
                    SUM(CASE WHEN test_status = 1 THEN 1 ELSE 0 END) as working_tracks,
                    SUM(CASE WHEN test_status = 0 THEN 1 ELSE 0 END) as failed_tracks,
                    SUM(CASE WHEN probe_failure_count >= 5 THEN 1 ELSE 0 END) as critical_tracks
                FROM stream_tracks
            """)
            stats = dict(zip(['total', 'working', 'failed', 'critical'], c.fetchone()))
            
            # 获取失效URL统计
            c.execute("""
                SELECT 
                    COUNT(*) as total_invalid,
                    AVG(failure_count) as avg_failures,
                    SUM(CASE WHEN last_success_time IS NOT NULL THEN 1 ELSE 0 END) as recovered
                FROM invalid_urls
            """)
            invalid_stats = dict(zip(['total', 'avg_failures', 'recovered'], c.fetchone()))
            
            return BaseResponse.success(data={
                'tracks': stats,
                'invalid_urls': invalid_stats
            })
        except Exception as e:
            logger.debug(f"获取统计信息失败: {str(e)}")
            return BaseResponse.error(message="获取统计信息失败")