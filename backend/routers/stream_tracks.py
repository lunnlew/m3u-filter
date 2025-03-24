from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import sqlite3
from datetime import datetime
import aiohttp
import asyncio
import logging

from sqlalchemy import False_
from models import StreamTrack
from database import get_db_connection
from typing import Dict
from models import BaseResponse
from ping3 import ping
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logger = logging.getLogger(__name__)

# 在文件开头导入部分添加
import yt_dlp
import os
import time

# 修改 test_stream_url 函数，添加测速逻辑
async def test_stream_url(url: str, track_id: int = None) -> tuple[bool, float, dict]:
    try:
        start_time = datetime.now()
        logger.info(f"开始测试流媒体URL: {url}")

        # 创建测试任务
        tasks = [
            probe_stream(url),           # FFmpeg探测任务
            ping_url(url),              # Ping测试任务
            test_download_speed(url, track_id) if track_id else None  # 测速任务
        ]
        
        # 过滤掉None任务并并行执行
        results = await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)
        
        # 初始化结果变量
        probe_result = None
        ping_time = 0.0
        speed_info = {
            'download_speed': 0.0,
            'speed_test_status': False,
            'speed_test_time': None
        }

        # 解析结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务 {i} 执行失败: {str(result)}")
                continue
                
            if i == 0:  # FFmpeg探测结果
                probe_result = result
            elif i == 1:  # Ping结果
                ping_time = result if isinstance(result, (int, float)) else 0.0
            elif i == 2 and track_id:  # 测速结果
                speed_info = result

        # 计算总耗时
        duration = (datetime.now() - start_time).total_seconds()

        # 初始化流媒体信息
        stream_info = {
            'video_codec': '',
            'audio_codec': '',
            'resolution': '',
            'bitrate': 0,
            'frame_rate': 0,
            'ping_time': ping_time,
            'download_speed': speed_info.get('download_speed', 0.0),
            'speed_test_status': speed_info.get('speed_test_status', False),
            'speed_test_time': speed_info.get('speed_test_time')
        }

        # 只有在probe_result有效时才解析流信息
        if probe_result and isinstance(probe_result, dict) and 'streams' in probe_result:
            for stream in probe_result.get('streams', []):
                if 'codec_type' in stream:
                    if stream['codec_type'] == 'video':
                        stream_info['video_codec'] = stream.get('codec_name', '')
                        if stream.get('width') and stream.get('height'):
                            stream_info['resolution'] = f"{stream['width']}x{stream['height']}"
                        if stream.get('r_frame_rate'):
                            try:
                                num, den = map(int, stream['r_frame_rate'].split('/'))
                                if den != 0:
                                    stream_info['frame_rate'] = round(num / den, 2)
                            except (ValueError, ZeroDivisionError):
                                pass
                    elif stream['codec_type'] == 'audio':
                        stream_info['audio_codec'] = stream.get('codec_name', '')
                        if stream.get('bit_rate'):
                            try:
                                stream_info['bitrate'] = int(stream['bit_rate']) // 1000
                            except (ValueError, TypeError):
                                pass

        # 根据测速结果判断状态
        status = speed_info.get('speed_test_status', False)
        logger.info(f"流媒体测试完成: {url}, 延迟: {duration}秒, 信息: {stream_info}")
        return status, duration, stream_info

    except Exception as e:
        logger.error(f"测试流媒体URL时发生错误: {url}, {str(e)}")
        return False, 0.0, {
            'video_codec': '',
            'audio_codec': '',
            'resolution': '',
            'bitrate': 0,
            'frame_rate': 0,
            'ping_time': 0.0,
            'download_speed': 0.0,
            'speed_test_status': False,
            'speed_test_time': None
        }

async def probe_stream(url: str) -> dict:
    """FFmpeg探测流"""
    # 检查ffmpeg是否可用
    try:
        import ffmpeg
    except ImportError:
        logger.error("ffmpeg-python库未安装，请先安装该库")
        raise ImportError("ffmpeg-python库未安装，请先安装该库")

    logger.info(f"开始测试流媒体URL: {url}")
    # 设置ffmpeg探测参数
    probe_options = {
        'v': 'error',      # 只显示错误信息
        'timeout': '10',   # 设置超时时间为10秒
        'show_entries': 'stream=codec_name,width,height,codec_type,bit_rate,r_frame_rate',
    }
    # 异步执行ffmpeg探测，并设置超时处理
    async def probe_with_timeout(timeout):
        proc = None
        try:
            probe_future = asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.probe(url, **probe_options)
            )
            return await asyncio.wait_for(probe_future, timeout)
        except ffmpeg.Error as fe:
            raise Exception(f"FFmpeg探测失败: {url}, {str(getattr(fe, 'stderr', str(fe)))}")
        except asyncio.TimeoutError:
            # 在超时时尝试终止ffmpeg进程
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'probe' in proc.info['name'].lower():
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            raise TimeoutError("probe探测超时")
        except Exception as e:
            logger.error(f"probe探测失败: {url}, {str(e)}")
            raise

    probe = await probe_with_timeout(5)
    logger.error(f"ffmpeg探测成功: {url}")
    return probe

async def test_stream_track(track_id: int):
    logger.info(f"开始测试频道ID: {track_id}")
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            with get_db_connection() as conn:  # 增加连接超时
                c = conn.cursor()
                c.execute("SELECT url FROM stream_tracks WHERE id = ?", (track_id,))
                result = c.fetchone()
                if not result:
                    logger.warning(f"未找到频道ID: {track_id}")
                    return
                
                url = result[0]
                # 传入 track_id 以启用测速功能
                status, speed, stream_info = await test_stream_url(url, track_id)
                
                # 更新测试结果
                c.execute(
                    """UPDATE stream_tracks SET 
                        test_status = ?, test_latency = ?, video_codec = ?, 
                        audio_codec = ?, resolution = ?, bitrate = ?, 
                        frame_rate = ?, ping_time = ?, last_test_time = ?
                       WHERE id = ?""",
                    (status, speed, stream_info.get('video_codec'), 
                     stream_info.get('audio_codec'), stream_info.get('resolution'), 
                     stream_info.get('bitrate'), stream_info.get('frame_rate'),
                     stream_info.get('ping_time'), datetime.now().isoformat(), 
                     track_id)
                )
                conn.commit()
                logger.info(f"频道测试结果已更新: {track_id}, 状态: {status}, 延迟: {speed}秒")
                break
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"数据库锁定，第{attempt+1}次重试...")
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"更新测试结果失败: {str(e)}")
                raise

router = APIRouter()

@router.get("/stream-tracks")
async def get_stream_tracks(
    name: Optional[str] = None,
    group_title: Optional[str] = None,
    source_id: Optional[int] = None,
    test_status: Optional[bool] = False,
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
        if test_status is not None and test_status:
            where_clause += " AND st.test_status =?"
            params.append(test_status)

        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM stream_tracks st {where_clause}"
        c.execute(count_query, params)
        total = c.fetchone()[0]

        # 计算分页参数
        offset = (page - 1) * page_size
        # 获取分页数据，包含source信息
        query = f"""SELECT st.*, ss.name as source_name, ss.url as source_url, ss.type as source_type, COALESCE(st.download_speed, 0) as download_speed 
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
        # c.execute("SELECT id FROM stream_tracks WHERE last_test_time < datetime('now','-6 hours') OR last_test_time IS NULL")
        c.execute("SELECT id FROM stream_tracks")
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

# 创建线程池执行器
ffmpeg_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ffmpeg_worker")
db_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_worker")

async def process_batch_tasks(task_id: int, track_ids: list):
    logger.info(f"开始处理批量任务 {task_id}")
    
    # 设置并发限制
    semaphore = asyncio.Semaphore(5)
    batch_size = 10
    results = {}
    
    try:
        async def process_single_track(track_id: int):
            async with semaphore:
                try:
                    # 获取URL
                    url = await asyncio.get_event_loop().run_in_executor(
                        db_executor,
                        partial(get_track_url, track_id)
                    )
                    if not url:
                        return {
                            'track_id': track_id,
                            'status': 'failed',
                            'error': 'URL not found',
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    # 在线程池中执行FFmpeg探测
                    status, speed, stream_info = await asyncio.get_event_loop().run_in_executor(
                        ffmpeg_executor,
                        partial(sync_test_stream_url, url, track_id)
                    )
                    
                    # 在单独的线程中更新数据库
                    await asyncio.get_event_loop().run_in_executor(
                        db_executor,
                        partial(update_track_result, track_id, status, speed, stream_info)
                    )
                    
                    return {
                        'track_id': track_id,
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"处理track_id={track_id}失败: {str(e)}")
                    return {
                        'track_id': track_id,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }

        # 分批处理任务
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            batch_tasks = [process_single_track(track_id) for track_id in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            
            # 批量更新任务状态
            processed_count = i + len(batch)
            await asyncio.get_event_loop().run_in_executor(
                db_executor,
                partial(
                    update_task_progress,
                    task_id,
                    processed_count,
                    len(track_ids),
                    batch_results
                )
            )
            
            # 短暂暂停
            await asyncio.sleep(0.1)
        
        # 标记任务完成
        await asyncio.get_event_loop().run_in_executor(
            db_executor,
            partial(mark_task_completed, task_id, results)
        )
            
    except Exception as e:
        logger.error(f"批量任务处理失败 {task_id}: {str(e)}")
        await asyncio.get_event_loop().run_in_executor(
            db_executor,
            partial(mark_task_failed, task_id, str(e))
        )

def get_track_url(track_id: int) -> str:
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT url FROM stream_tracks WHERE id = ?", (track_id,))
        result = c.fetchone()
        return result[0] if result else None

def sync_test_stream_url(url: str, track_id: int) -> tuple[bool, float, dict]:
    # 将异步的test_stream_url转换为同步版本
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_stream_url(url, track_id))
    finally:
        loop.close()

async def test_download_speed(url: str, track_id: int) -> dict:
    """使用yt-dlp库测试流媒体下载速度"""
    logger.info(f"开始使用yt-dlp测速: {url}")
    start_time = time.time()
    downloaded = 0
    speed = 0.0
    status = False
    
    try:
        # 配置yt-dlp选项
        ydl_opts = {
            'format': 'best',  # 选择最佳质量
            'quiet': True,     # 不显示下载进度
            'no_warnings': True,
            'extract_flat': False,
        }

        # 创建下载器实例并获取媒体片段信息
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and 'fragments' in info:
                # 获取媒体片段列表
                fragments = info.get('fragments', [])
                if fragments:
                    # 获取基础URL，用于处理相对路径
                    base_url = info.get('url', '')
                    parsed_base = urlparse(base_url or url)
                    base_url = f"{parsed_base.scheme}://{parsed_base.netloc}{os.path.dirname(parsed_base.path)}/"

                    # 选择前几个片段进行测试
                    test_fragments = fragments[:3]  # 测试前3个片段
                    total_size = 0
                    total_time = 0

                    # 测试每个片段的下载速度
                    async with aiohttp.ClientSession() as session:
                        for fragment in test_fragments:
                            fragment_url = fragment.get('url', '')
                            if not fragment_url:
                                continue
                            
                            # 处理相对路径
                            if not urlparse(fragment_url).netloc:
                                fragment_url = urljoin(base_url, fragment_url)

                            start = time.time()
                            try:
                                async with session.get(fragment_url) as response:
                                    if response.status == 200:
                                        chunk = await response.read()
                                        total_size += len(chunk)
                                        total_time += time.time() - start
                            except Exception as e:
                                logger.error(f"片段下载失败: {fragment_url}, {str(e)}")
                                continue

                    # 计算平均速度
                    if total_time > 0:
                        speed = (total_size / (1024 * 1024)) / total_time
                        status = speed > 0
                        downloaded = total_size
                        logger.info(f"测速结果: {url} 速度: {speed:.2f}MB/s 时长: {total_time:.1f}s")

            else:
                # 如果不是分片格式，使用常规下载测试
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            start = time.time()
                            chunk_size = 8192
                            while time.time() - start < 5:  # 测试5秒
                                chunk = await response.content.read(chunk_size)
                                if not chunk:
                                    break
                                downloaded += len(chunk)
                            
                            duration = max(time.time() - start, 0.1)
                            speed = (downloaded / (1024 * 1024)) / duration
                            status = speed > 0

    except Exception as e:
        logger.error(f"测速失败: {url}, {str(e)}")
        status = False

    return {
        'download_speed': round(speed, 2),
        'speed_test_status': status,
        'speed_test_time': datetime.now().isoformat(),
        'downloaded_bytes': downloaded,
        'duration_seconds': round(time.time() - start_time, 2)
    }

def update_track_result(track_id: int, status: bool, speed: float, stream_info: dict):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """UPDATE stream_tracks SET 
                test_status = ?, test_latency = ?, video_codec = ?, 
                audio_codec = ?, resolution = ?, bitrate = ?, 
                frame_rate = ?, ping_time = ?, last_test_time = ?,
                download_speed = ?, speed_test_status = ?, speed_test_time = ?
               WHERE id = ?""",
            (status, speed, stream_info.get('video_codec'), 
             stream_info.get('audio_codec'), stream_info.get('resolution'),
             stream_info.get('bitrate'), stream_info.get('frame_rate'),
             stream_info.get('ping_time'), datetime.now().isoformat(),
             stream_info.get('download_speed', 0.0),
             stream_info.get('speed_test_status', False),
             stream_info.get('speed_test_time'),
             track_id)
        )
        conn.commit()

def update_task_progress(task_id: int, processed_count: int, total_count: int, batch_results: list):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """UPDATE stream_tasks SET
                processed_items = ?,
                progress = ?,
                result = ?,
                updated_at = ?
               WHERE id = ?""",
            (processed_count, processed_count/total_count,
             str({str(r['track_id']): r for r in batch_results}),
             datetime.now().isoformat(), task_id)
        )
        conn.commit()

def mark_task_completed(task_id: int, results: dict):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """UPDATE stream_tasks SET
                status = 'completed',
                progress = 1.0,
                result = ?,
                updated_at = ?
               WHERE id = ?""",
            (str(results), datetime.now().isoformat(), task_id)
        )
        conn.commit()

def mark_task_failed(task_id: int, error: str):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """UPDATE stream_tasks SET
                status = 'failed',
                result = ?,
                updated_at = ?
               WHERE id = ?""",
            (f"System Error: {error}", datetime.now().isoformat(), task_id)
        )
        conn.commit()

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


async def ping_url(url: str) -> float:
    try:
        # 解析URL以提取域名或IP地址
        parsed_url = urlparse(url)
        host = parsed_url.hostname

        if not host:
            logger.error(f"无法解析URL: {url}")
            return 0.0

        # 使用ping3库测试域名或IP地址
        ping_time = ping(host, unit='ms')
        print(f"Ping时间: {ping_time} ms")        
        if ping_time is None:
            logger.error(f"Ping失败: 无法到达 {host}")
            return 0.0
        return ping_time
    except Exception as e:
        logger.error(f"Ping测试时发生错误: {str(e)}")
        return 0.0
