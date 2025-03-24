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
import re  # 添加 re 模块导入

logger = logging.getLogger(__name__)

# 在文件开头导入部分添加
import yt_dlp
import os
import time

# 修改 test_stream_url 函数，添加测速逻辑
async def test_stream_url(url: str, track_id: int = None) -> tuple[bool, float, dict]:
    try:
        start_time = datetime.now()
        logger.info(f"开始测试流媒体URL: {url}, track_id: {track_id}")

        # 首先执行探测任务获取码率信息
        logger.debug(f"开始执行FFmpeg探测: {url}")
        probe_result = await probe_stream(url)
        logger.debug(f"FFmpeg探测完成: {url}")
        
        # 从探测结果中获取码率
        logger.debug(f"开始提取码率信息: {url}")
        bitrate = await extract_bitrate(probe_result)
        logger.debug(f"码率提取完成: {url}, bitrate: {bitrate/1024/1024:.2f}Mbps")
        
        # 执行ping测试
        logger.debug(f"开始执行Ping测试: {url}")
        ping_time = await ping_url(url)
        logger.debug(f"Ping测试完成: {url}, ping_time: {ping_time}ms")
        
        # 如果提供了track_id，则创建并执行下载速度测试
        logger.debug(f"开始执行下载速度测试: {url}")
        speed_info = await test_download_speed(url, track_id, bitrate) if track_id else {
            'download_speed': 0.0,
            'speed_test_status': False,
            'speed_test_time': None
        }
        logger.debug(f"下载速度测试完成: {url}, speed_info: {speed_info}")

        # 计算总耗时
        duration = (datetime.now() - start_time).total_seconds()

        # 解析流媒体信息
        logger.debug(f"开始解析流媒体信息: {url}")
        stream_info = await extract_stream_info(probe_result, ping_time, speed_info)
        logger.debug(f"流媒体信息解析完成: {url}, stream_info: {stream_info}")

        # 根据速度测试结果确定状态
        status = speed_info.get('speed_test_status', False)
        logger.info(f"流媒体测试完成: {url}, 状态: {status}, 延迟: {duration}秒, 信息: {stream_info}")
        return status, duration, stream_info

    except Exception as e:
        logger.error(f"测试流媒体URL时发生错误: {url}, 错误信息: {str(e)}", exc_info=True)
        return False, 0.0, get_default_stream_info()

async def extract_bitrate(probe_result: dict) -> int:
    """从probe结果中提取码率信息"""
    DEFAULT_BITRATE = 5 * 1024 * 1024  # 默认5Mbps
    
    if not probe_result or not isinstance(probe_result, dict):
        return DEFAULT_BITRATE
        
    try:
        # 1. 从format信息中获取总码率
        if 'format' in probe_result:
            format_bitrate = probe_result['format'].get('bit_rate')
            if format_bitrate:
                return int(format_bitrate)
        
        # 2. 从视频流中获取码率
        if 'streams' in probe_result:
            video_bitrate = 0
            audio_bitrate = 0
            
            for stream in probe_result.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_bitrate = extract_video_bitrate(stream)
                elif stream.get('codec_type') == 'audio':
                    audio_bitrate = int(stream.get('bit_rate', 0))
            
            total_stream_bitrate = video_bitrate + audio_bitrate
            if total_stream_bitrate > 0:
                return total_stream_bitrate
        
        return DEFAULT_BITRATE
        
    except (ValueError, TypeError) as e:
        logger.warning(f"解析码率时出错: {str(e)}, 使用默认值5Mbps")
        return DEFAULT_BITRATE

def extract_video_bitrate(stream: dict) -> int:
    """从视频流中提取码率"""
    bitrate_sources = [
        ('bit_rate', None),
        ('max_bit_rate', None),
        ('tags.BPS', 'tags'),
        ('tags.variant_bitrate', 'tags'),
        ('tags.BANDWIDTH', 'tags')
    ]
    
    for key, parent in bitrate_sources:
        try:
            if parent:
                value = stream.get(parent, {}).get(key.split('.')[-1], 0)
            else:
                value = stream.get(key, 0)
            if value:
                return int(value)
        except (ValueError, TypeError):
            continue
    
    return 0

def parse_test_results(results: list, track_id: int) -> tuple:
    """解析测试结果"""
    probe_result = None
    ping_time = 0.0
    speed_info = {
        'download_speed': 0.0,
        'speed_test_status': False,
        'speed_test_time': None
    }

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

    return probe_result, ping_time, speed_info

def get_default_stream_info() -> dict:
    """获取默认的流媒体信息"""
    return {
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
        'show_entries': (
            'stream=codec_name,width,height,codec_type,bit_rate,r_frame_rate,'
            'avg_frame_rate,max_bit_rate,tags,'  # 添加平均帧率和最大码率
            'format=bit_rate,size,duration'       # 添加格式信息
        ),
        'show_format': None,  # 显示格式信息
        'show_streams': None  # 显示所有流信息
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
            with get_db_connection() as conn:
                logger.debug(f"获取数据库连接成功: track_id={track_id}")
                c = conn.cursor()
                c.execute("SELECT url FROM stream_tracks WHERE id = ?", (track_id,))
                result = c.fetchone()
                if not result:
                    logger.warning(f"未找到频道ID: {track_id}")
                    return
                
                url = result[0]
                logger.debug(f"开始测试频道URL: {url}, track_id={track_id}")
                status, speed, stream_info = await test_stream_url(url, track_id)
                logger.debug(f"频道测试完成: track_id={track_id}, status={status}, speed={speed}")
                
                # 更新测试结果
                logger.debug(f"开始更新频道测试结果: track_id={track_id}")
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
                logger.info(f"频道测试结果已更新: track_id={track_id}, 状态={status}, 延迟={speed}秒")
                break
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"数据库锁定，第{attempt+1}次重试: track_id={track_id}")
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"更新测试结果失败: track_id={track_id}, 错误信息: {str(e)}", exc_info=True)
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

async def test_download_speed(url: str, track_id: int, bitrate: int) -> dict:
    """
    使用ffmpeg测试流媒体下载速度
    返回:
        dict: 包含以下字段:
            - download_speed: 下载速度 (Mbps)
            - speed_test_status: 测试状态
            - speed_test_time: 测试时间
            - downloaded_bytes: 已下载字节数 (bytes)
            - duration_seconds: 测试持续时间 (秒)
    """
    start_time = time.time()
    downloaded = 0
    speed = 0.0
    status = False
    
    try:
        import ffmpeg
        
        # 创建ffmpeg进程，设置超时和输出格式
        process = (
            ffmpeg
            .input(url, t=10)  # 限制读取时间为10秒
            .output('pipe:', format='null')  # 输出到空设备
            .global_args(
                '-loglevel', 'info',  # 设置日志级别
                '-stats',             # 显示详细的统计信息
                '-progress', 'pipe:2' # 将进度信息输出到stderr
            )
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        stderr_text = ''
        current_speed = 0.0
        downloaded = 0

        async def read_output():
            nonlocal stderr_text, current_speed, downloaded
            start_time = time.time()
            while True:
                try:
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        process.stderr.readline
                    )
                    if not line:
                        break
                    
                    line = line.decode('utf-8', errors='ignore')
                    stderr_text += line
                    
                    # 解析实时速度信息
                    if line.startswith('frame='):
                        # 解析时间和速度
                        time_match = re.search(r'time=(\d+):(\d+):(\d+.\d+)', line)
                        speed_match = re.search(r'speed=(\d+.\d+)x', line)
                        
                        if time_match and speed_match:
                            # 计算已处理的时间（秒）
                            h, m, s = time_match.groups()
                            processed_time = float(h) * 3600 + float(m) * 60 + float(s)
                            
                            # 获取速度倍率
                            speed_factor = float(speed_match.group(1))
                            
                            # 修改：使用传入的码率计算实际下载速度，单位改为 Mbps
                            current_speed = bitrate * speed_factor / (1024 * 1024)  # 转换为 Mbps
                            
                            # 计算已下载数据量
                            downloaded = bitrate * processed_time
                            duration = time.time() - start_time
                            if duration > 0:
                                current_speed = (downloaded / duration) / (1024 * 1024 / 8)  # 转换为 Mbps
                                
                except Exception as e:
                    logger.error(f"读取输出错误: {str(e)}")
                    break

        # 启动输出读取任务
        read_task = asyncio.create_task(read_output())
        
        try:
            # 等待进程完成，最多10秒
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, process.wait),
                timeout=10
            )
        except asyncio.TimeoutError:
            logger.warning(f"测速超时: {url}")
        finally:
            # 确保进程被终止和清理
            try:
                process.kill()
            except:
                pass
            read_task.cancel()
            
            # 设置最终状态
            status = current_speed > 0
            speed = current_speed
            logger.info(f"测速完成: {url}, 速度: {speed:.2f}Mbps")

    except Exception as e:
        logger.error(f"测速失败: {url}, {str(e)}")
        status = False
        speed = 0.0
        downloaded = 0

    return {
        'download_speed': round(speed, 2),  # 单位: Mbps
        'speed_test_status': status,
        'speed_test_time': datetime.now().isoformat(),
        'downloaded_bytes': downloaded,
        'duration_seconds': round(time.time() - start_time, 2)
    }

def update_track_result(track_id: int, status: bool, speed: float, stream_info: dict):
    with get_db_connection() as conn:
        c = conn.cursor()
        # 将 Mbps 转换为 MB/s (除以8)
        download_speed = round(stream_info.get('download_speed', 0.0) / 8, 2)
        
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
             download_speed,  # 使用转换后的速度值
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

def extract_frame_rate(stream: dict) -> float:
    """从视频流中提取帧率"""
    for rate_key in ['r_frame_rate', 'avg_frame_rate']:
        if stream.get(rate_key):
            try:
                num, den = map(int, stream[rate_key].split('/'))
                if den != 0:
                    return round(num / den, 2)
            except (ValueError, ZeroDivisionError):
                continue
    return 0.0
                
async def extract_stream_info(probe_result: dict, ping_time: float, speed_info: dict) -> dict:
    """Extract stream information from probe result"""
    stream_info = get_default_stream_info()
    stream_info.update({
        'ping_time': ping_time,
        'download_speed': speed_info.get('download_speed', 0.0),
        'speed_test_status': speed_info.get('speed_test_status', False),
        'speed_test_time': speed_info.get('speed_test_time')
    })

    if probe_result and isinstance(probe_result, dict) and 'streams' in probe_result:
        # 获取码率
        bitrate = await extract_bitrate(probe_result)
        stream_info['bitrate'] = bitrate // 1000  # 转换为 Kbps
        
        for stream in probe_result.get('streams', []):
            if 'codec_type' in stream:
                
                # 在 extract_stream_info 中使用
                if stream['codec_type'] == 'video':
                    stream_info['video_codec'] = stream.get('codec_name', '')
                    if stream.get('width') and stream.get('height'):
                        stream_info['resolution'] = f"{stream['width']}x{stream['height']}"
                    stream_info['frame_rate'] = extract_frame_rate(stream)
                elif stream['codec_type'] == 'audio':
                    stream_info['audio_codec'] = stream.get('codec_name', '')

    return stream_info
