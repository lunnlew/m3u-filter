from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional
import asyncio
from sync import sync_epg_source, sync_stream_source
from database import get_db_connection
from routers.stream_tracks import test_all_tracks, cleanup_invalid_tracks, maintain_invalid_urls
from routers.filter_rule_sets import generate_m3u_file, generate_txt_file

import logging
logger = logging.getLogger(__name__)

# 获取当前事件循环
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# 创建调度器时指定事件循环
scheduler = AsyncIOScheduler(event_loop=loop)

def schedule_test_stream_tracks():
    """调度直播源测试任务"""
    scheduler.add_job(
        test_all_tracks,
        trigger=IntervalTrigger(hours=3),
        id='test_stream_tracks',
        name='Test All Stream Tracks',
        replace_existing=True
    )

def schedule_sync_epg_sources():
    """调度EPG数据源同步任务"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, sync_interval FROM epg_sources WHERE active = 1")
        sources = c.fetchall()
        
        for source_id, name, interval in sources:
            hours = interval if interval is not None else 6
            scheduler.add_job(
                sync_epg_source,
                trigger=IntervalTrigger(hours=hours),
                args=[source_id],
                id=f'sync_source_{source_id}',
                name=f'Sync EPG Source: {name}',
                replace_existing=True
            )

def schedule_sync_stream_sources():
    """调度流数据源同步任务"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, sync_interval FROM stream_sources WHERE active = 1")
        sources = c.fetchall()
        
        for source_id, name, interval in sources:
            hours = interval if interval is not None else 6
            scheduler.add_job(
                sync_stream_source,
                trigger=IntervalTrigger(hours=hours),
                args=[source_id],
                id=f'sync_stream_{source_id}',
                name=f'Sync Stream Source: {name}',
                replace_existing=True
            )

def schedule_generate_m3u_files():
    """调度生成M3U Txt文件任务"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, sync_interval FROM filter_rule_sets WHERE enabled = 1")
        rule_sets = c.fetchall()
        
        for set_id, name, interval in rule_sets:
            hours = interval if interval is not None else 6
            scheduler.add_job(
                generate_txt_file,
                trigger=IntervalTrigger(hours=hours),
                args=[set_id],
                id=f'generate_m3u_txt_{set_id}',
                name=f'Generate M3U Txt for Rule Set: {name}',
                replace_existing=True
            )

def schedule_generate_txt_files():
    """调度生成M3U文件任务"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, sync_interval FROM filter_rule_sets WHERE enabled = 1")
        rule_sets = c.fetchall()
        
        for set_id, name, interval in rule_sets:
            hours = interval if interval is not None else 6
            scheduler.add_job(
                generate_m3u_file,
                trigger=IntervalTrigger(hours=hours),
                args=[set_id],
                id=f'generate_m3u_{set_id}',
                name=f'Generate M3U for Rule Set: {name}',
                replace_existing=True
            )


def init_scheduler():
    """初始化调度器并添加所有任务"""
    scheduler.remove_all_jobs()
    schedule_test_stream_tracks()
    schedule_sync_epg_sources()
    schedule_sync_stream_sources()
    schedule_generate_m3u_files()
    schedule_generate_txt_files()
    
    # 添加清理任务
    scheduler.add_job(
        cleanup_invalid_tracks,
        trigger=IntervalTrigger(hours=12),  # 每12小时执行一次
        id='cleanup_invalid_tracks',
        name='Cleanup Invalid Tracks',
        replace_existing=True,
        misfire_grace_time=3600  # 允许1小时的任务延迟
    )
    
    # 添加URL状态维护任务
    scheduler.add_job(
        maintain_invalid_urls,
        trigger=IntervalTrigger(hours=6),  # 每6小时执行一次
        id='maintain_invalid_urls',
        name='Maintain Invalid URLs',
        replace_existing=True,
        misfire_grace_time=3600
    )

def start_scheduler():
    """启动调度器"""
    if scheduler.running:
        logger.info("Scheduler is already running, skipping initialization")
        return
        
    logger.info("Initializing scheduler...")
    init_scheduler()
    
    scheduler.start()
    
    # 添加日志记录所有已配置的任务
    jobs = scheduler.get_jobs()
    for job in jobs:
        next_run = job.next_run_time.isoformat() if job.next_run_time else "Not scheduled"
        logger.info(f"Scheduled job: {job.name}, next run: {next_run}")
    
    logger.info("Scheduler started successfully")

def update_source_schedule(source_id: int):
    """更新指定数据源的同步计划"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name, sync_interval, active FROM epg_sources WHERE id = ?", (source_id,))
        result = c.fetchone()
        
        if not result:
            return
        
        name, interval, active = result
        job_id = f'sync_source_{source_id}'
        
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        if active:
            hours = interval if interval is not None else 6
            scheduler.add_job(
                sync_epg_source,
                trigger=IntervalTrigger(hours=hours),
                args=[source_id],
                id=job_id,
                name=f'Sync EPG Source: {name}',
                replace_existing=True
            )

def update_stream_schedule(source_id: int):
    """更新指定数据源的同步计划"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name, sync_interval, active FROM stream_sources WHERE id = ?", (source_id,))
        result = c.fetchone()
        
        if not result:
            return
        
        name, interval, active = result
        job_id = f'sync_stream_{source_id}'
        
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        if active:
            hours = interval if interval is not None else 6
            scheduler.add_job(
                sync_stream_source,
                trigger=IntervalTrigger(hours=hours),
                args=[source_id],
                id=job_id,
                name=f'Sync EPG Source: {name}',
                replace_existing=True
            )

def get_source_next_run(source_id: int) -> Optional[str]:
    """获取指定数据源下次同步的时间"""
    job = scheduler.get_job(f'sync_source_{source_id}')
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None