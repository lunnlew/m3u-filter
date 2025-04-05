from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Tuple
import sqlite3
from datetime import datetime
import aiohttp
import asyncio

from models import StreamTrack
from database import get_db_connection
from typing import Dict
from models import BaseResponse
from ping3 import ping
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import re  # 添加 re 模块导入
import time
from .blocked_domains import should_skip_domain, record_domain_failure, get_domain_key
from utils import *

import logging
logger = logging.getLogger(__name__)

# 添加批量更新队列
failure_update_queue = []
FAILURE_BATCH_SIZE = 50
last_failure_update = time.time()
FAILURE_UPDATE_INTERVAL = 60  # 秒

async def increment_failure_count(track_id: int, url: str):
    """增加流媒体源的失败计数"""
    global failure_update_queue, last_failure_update
    
    try:
        # 如果提供了URL，直接使用；否则才查询数据库
        if not url:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT url FROM stream_tracks WHERE id = ?", (track_id,))
                result = c.fetchone()
                if not result:
                    return
                url = result[0]
        
        # 获取域名键值并记录失败
        domain_key = get_domain_key(url)
        if domain_key:
            # 等待域名失败记录完成
            await record_domain_failure(domain_key, "Stream probe failed")
    
        # 添加到更新队列
        failure_update_queue.append({
            'track_id': track_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # 检查是否需要执行批量更新
        current_time = time.time()
        if (len(failure_update_queue) >= FAILURE_BATCH_SIZE or 
            current_time - last_failure_update >= FAILURE_UPDATE_INTERVAL):
            await batch_update_failures()
            
    except Exception as e:
        logger.error(f"增加失败计数时出错: {str(e)}")

async def batch_update_failures():
    """批量更新失败计数"""
    global failure_update_queue, last_failure_update
    
    if not failure_update_queue:
        return
        
    updates = failure_update_queue.copy()
    failure_update_queue.clear()
    last_failure_update = time.time()
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.executemany("""
                UPDATE stream_tracks 
                SET probe_failure_count = COALESCE(probe_failure_count, 0) + 1,
                    last_failure_time = ?
                WHERE id = ?
            """, [(u['timestamp'], u['track_id']) for u in updates])
            conn.commit()
            logger.debug(f"批量更新了 {len(updates)} 个频道的失败计数")
    except Exception as e:
        logger.error(f"批量更新失败计数时出错: {str(e)}")
        # 如果更新失败，将未更新的记录放回队列
        failure_update_queue.extend(updates)

async def test_stream_url(url: str, track_id: int) -> tuple[bool, float, dict]:
    start_time = datetime.now()
    logger.info(f"开始测试流媒体URL: {url}, track_id: {track_id}")

    # 检查域名是否在黑名单中
    domain_key = get_domain_key(url)
    if not domain_key:
        logger.error(f"无法获取有效的域名键值: {url}")
        if track_id:
            await increment_failure_count(track_id, url)  # 传入URL参数
        return False, 0.0, get_default_stream_info()
        
    if await should_skip_domain(domain_key):
        logger.warning(f"跳过测试黑名单域名: {url}")
        # 移除对失败计数的更新
        return False, 0.0, get_default_stream_info()

    try:
        # 检测协议类型
        protocol = detect_stream_protocol(url)
        logger.info(f"检测到流媒体协议: {protocol}, URL: {url}")
        
        # 根据协议类型选择探测方法
        if protocol == "hls":
            probe_result = await probe_hls_stream(url)
        elif protocol == "rtmp":
            probe_result = await probe_rtmp_stream(url)
        elif protocol == "rtsp":
            probe_result = await probe_rtsp_stream(url)
        else:  # 默认HTTP流
            probe_result = await probe_stream(url)
            
        if not probe_result:
            # 只有在域名键值有效时才记录失败
            if domain_key:
                await record_domain_failure(domain_key, "FFmpeg探测失败")
            if track_id:
                await increment_failure_count(track_id, url)
            return False, 0.0, get_default_stream_info()
            
        # 从探测结果中获取码率
        logger.debug(f"开始提取码率信息: {url}")
        bitrate = await extract_bitrate(probe_result)
        logger.debug(f"码率提取完成: {url}, bitrate: {bitrate/1024/1024:.2f}Mbps")
        
        # 执行ping测试
        logger.debug(f"开始执行Ping测试: {url}")
        ping_time = await ping_url(url)
        logger.debug(f"Ping测试完成: {url}, ping_time: {ping_time}ms")
        
        # 执行下载速度测试
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
        logger.info(f"流媒体测试完成: {url}, 状态: {status}, 延迟: {duration}秒")
        return status, duration, stream_info

    except Exception as e:
        # 只有在域名键值有效时才记录失败
        if domain_key:
            asyncio.create_task(record_domain_failure(domain_key, str(e)))
        logger.error(f"测试流媒体URL时发生错误: {url}, 错误信息: {str(e)}")
        
        if track_id:
            await increment_failure_count(track_id, url)
            
        return False, 0.0, get_default_stream_info()

async def probe_stream(url: str) -> dict:
    """FFmpeg探测流"""
    try:
        import ffmpeg
    except ImportError:
        logger.error("ffmpeg-python库未安装")
        return {}

    # 设置ffmpeg探测参数
    probe_options = {
        'v': 'error',      # 只显示错误信息
        'timeout': '10',   # 设置超时时间为10秒
        'show_entries': (
            'stream=codec_name,width,height,codec_type,bit_rate,r_frame_rate,'
            'avg_frame_rate,max_bit_rate,tags,'
            'format=bit_rate,size,duration'
        ),
        'show_format': None,
        'show_streams': None
    }
    # 异步执行ffmpeg探测，并设置超时处理
    async def probe_with_timeout(timeout):
        try:
            probe_future = asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.probe(url, **probe_options)
            )
            return await asyncio.wait_for(probe_future, timeout)
        except ffmpeg.Error as fe:
            logger.error(f"FFmpeg探测失败: {url}, {str(getattr(fe, 'stderr', str(fe)))}")
            return {}
        except asyncio.TimeoutError:
            logger.error(f"FFmpeg探测超时: {url}")
            # 清理超时进程
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'probe' in proc.info['name'].lower():
                        proc.kill()
            except Exception as e:
                logger.error(f"清理FFmpeg进程失败: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"FFmpeg探测出现未知错误: {url}, {str(e)}")
            return {}

    try:
        probe = await probe_with_timeout(5)
        if probe:
            logger.info(f"FFmpeg探测成功: {url}")
        return probe
    except Exception as e:
        logger.error(f"FFmpeg探测过程出现异常: {url}, {str(e)}")
        return {}

# 添加结果更新队列
track_result_queue = []
TRACK_RESULT_BATCH_SIZE = 20
last_track_result_update = time.time()
TRACK_RESULT_UPDATE_INTERVAL = 30  # 秒

async def batch_update_track_results():
    """批量更新频道测试结果"""
    global track_result_queue, last_track_result_update
    
    if not track_result_queue:
        return
        
    updates = track_result_queue.copy()
    track_result_queue.clear()
    last_track_result_update = time.time()
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.executemany(
                """UPDATE stream_tracks SET 
                    test_status = ?, test_latency = ?, video_codec = ?, 
                    audio_codec = ?, resolution = ?, bitrate = ?, 
                    frame_rate = ?, ping_time = ?, last_test_time = ?
                   WHERE id = ?""",
                [(u['status'], u['speed'], u['stream_info'].get('video_codec'),
                  u['stream_info'].get('audio_codec'), u['stream_info'].get('resolution'),
                  u['stream_info'].get('bitrate'), u['stream_info'].get('frame_rate'),
                  u['stream_info'].get('ping_time'), datetime.now().isoformat(),
                  u['track_id']) for u in updates]
            )
            conn.commit()
            logger.debug(f"批量更新了 {len(updates)} 个频道的测试结果")
    except Exception as e:
        logger.error(f"批量更新测试结果时出错: {str(e)}")
        # 如果更新失败，将未更新的记录放回队列
        track_result_queue.extend(updates)

async def test_stream_track(track_id: int):
    logger.info(f"开始测试频道ID: {track_id}")
    global track_result_queue, last_track_result_update
    
    try:
        with get_db_connection() as conn:
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
            
            # 将测试结果添加到更新队列
            track_result_queue.append({
                'track_id': track_id,
                'status': status,
                'speed': speed,
                'stream_info': stream_info
            })
            
            # 检查是否需要执行批量更新
            current_time = time.time()
            if (len(track_result_queue) >= TRACK_RESULT_BATCH_SIZE or 
                current_time - last_track_result_update >= TRACK_RESULT_UPDATE_INTERVAL):
                await batch_update_track_results()
                
    except Exception as e:
        logger.error(f"测试频道失败: track_id={track_id}, 错误信息: {str(e)}", exc_info=True)
        raise

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

# 创建线程池执行器
ffmpeg_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ffmpeg_worker")
db_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_worker")

async def process_batch_tasks(task_id: int, track_ids: list):
    logger.info(f"开始处理批量任务 {task_id}")
    
    # 优化并发设置以提高处理速度
    semaphore = asyncio.Semaphore(15)  # 从5增加到15
    batch_size = 30  # 从10增加到30
    results = {}
    
    # 检查IPv6可访问性
    ipv6_available = await check_ipv6_connectivity()
    logger.info(f"IPv6可访问性检查结果: {ipv6_available}")
    
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
                    
                    # 检查URL是否是IPv6地址
                    parsed_url = urlparse(url)
                    host = parsed_url.hostname
                    is_ipv6 = ':' in host if host else False
                    
                    # 如果是IPv6地址但IPv6不可用，则跳过测试
                    if is_ipv6 and not ipv6_available:
                        logger.warning(f"跳过IPv6地址测试 (IPv6不可用): {url}")
                        return {
                            'track_id': track_id,
                            'status': 'skipped',
                            'error': 'IPv6 not available',
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

def get_track_url(track_id: int) -> Optional[str]:
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
    """支持不同协议的下载速度测试"""
    protocol = detect_stream_protocol(url)
    
    if protocol == 'hls':
        # HLS协议使用分段下载测试
        return await test_hls_download_speed(url, bitrate)
    elif protocol in ['rtmp', 'rtsp']:
        # RTMP/RTSP协议使用特殊参数
        return await test_rtmp_rtsp_download_speed(url, bitrate)
    else:
        # 默认HTTP流测试
        return await test_http_download_speed(url, bitrate)
async def test_hls_download_speed(url: str, bitrate: int) -> dict:
    """HLS协议下载速度测试"""
    speed = 0.0
    status = False
    speed_history = []
    buffer_health = 0.0
    
    try:
        import m3u8
        from urllib.parse import urlparse, urljoin
        
        # 解析主m3u8文件
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # 下载并解析m3u8文件
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {
                        'download_speed': 0.0,
                        'speed_test_status': False,
                        'speed_test_time': datetime.now().isoformat(),
                        'downloaded_bytes': 0,
                        'duration_seconds': 0.0,
                        'buffer_health': 0.0,
                        'stability_score': 0.0,
                        'quality_score': 0.0
                    }
                
                playlist = m3u8.loads(await resp.text())
                
                # 获取前3个片段进行测试
                segments = playlist.segments[:3] if playlist.segments else []
                if not segments:
                    raise ValueError("HLS播放列表中没有找到有效片段")
                
                total_size = 0
                total_duration = 0.0
                
                for segment in segments:
                    segment_url = urljoin(base_url, segment.uri)
                    try:
                        async with session.get(segment_url) as seg_resp:
                            if seg_resp.status == 200:
                                # 流式下载并计算速度
                                start_segment = time.time()
                                size = 0
                                async for chunk in seg_resp.content.iter_chunked(1024*1024):  # 1MB chunks
                                    size += len(chunk)
                                    elapsed = time.time() - start_segment
                                    if elapsed > 0:
                                        current_speed = (size * 8) / (elapsed * 1e6)  # Mbps
                                        speed_history.append(current_speed)
                                
                                total_size += size
                                total_duration += segment.duration or 0
                                
                                # 计算缓冲健康度
                                if bitrate > 0 and segment.duration or 0 > 0:
                                    segment_bitrate = (size * 8) / (segment.duration or 0 * 1e6)  # Mbps
                                    buffer_health = segment_bitrate / (bitrate / 1e6)
                    except Exception as e:
                        logger.warning(f"HLS片段下载失败: {segment_url}, 错误: {str(e)}")
                
                # 计算平均速度
                if total_duration > 0:
                    speed = (total_size * 8) / (total_duration * 1e6)  # Mbps
                    status = speed > (bitrate / 1e6 * 0.8)  # 速度达到码率的80%算成功
                
                # 计算稳定性
                stability_score = 0.0
                if len(speed_history) > 1:
                    avg_speed = sum(speed_history) / len(speed_history)
                    variance = sum((s - avg_speed) ** 2 for s in speed_history) / len(speed_history)
                    std_dev = variance ** 0.5
                    stability_score = max(0, 1 - (std_dev / avg_speed)) if avg_speed > 0 else 0.0
                
                # 计算质量评分
                quality_score = min(1.0, speed / (bitrate / 1e6)) if bitrate > 0 else 0.0
                
                return {
                    'download_speed': round(speed, 2),
                    'speed_test_status': status,
                    'speed_test_time': datetime.now().isoformat(),
                    'downloaded_bytes': total_size,
                    'duration_seconds': round(total_duration, 2),
                    'buffer_health': round(buffer_health, 2),
                    'stability_score': round(stability_score, 2),
                    'quality_score': round(quality_score, 2)
                }
                
    except Exception as e:
        logger.error(f"HLS测速失败: {url}, 错误: {str(e)}")
        return {
            'download_speed': 0.0,
            'speed_test_status': False,
            'speed_test_time': datetime.now().isoformat(),
            'downloaded_bytes': 0,
            'duration_seconds': 0.0,
            'buffer_health': 0.0,
            'stability_score': 0.0,
            'quality_score': 0.0
        }

async def test_rtmp_rtsp_download_speed(url: str, bitrate: int) -> dict:
    """RTMP/RTSP协议下载速度测试"""
    start_time = time.time()
    downloaded = 0
    speed = 0.0
    status = False
    speed_history = []
    buffer_health = 0.0
    
    try:
        import ffmpeg
        
        # 根据协议类型设置不同参数
        protocol = 'rtmp' if url.startswith('rtmp://') else 'rtsp'
        input_args = {
            'rtmp': {
                'rtmp_buffer': 1000,
                'rtmp_live': 'live',
                'timeout': 5000000  # 微秒
            },
            'rtsp': {
                'rtsp_transport': 'tcp',
                'rtsp_flags': 'prefer_tcp',
                'timeout': 5000000  # 微秒
            }
        }.get(protocol, {})
        
        process = (
            ffmpeg
            .input(url, **input_args, t=10)  # 测试10秒
            .output('pipe:', format='null')
            .global_args(
                '-loglevel', 'info',
                '-stats',
                '-progress', 'pipe:2'
            )
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        
        stderr_text = ''
        current_speed = 0.0
        downloaded = 0
        last_size = 0
        last_time = start_time
        
        async def read_output():
            nonlocal stderr_text, current_speed, downloaded, last_size, last_time, speed_history, buffer_health
            
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
                    
                    # 解析RTMP/RTSP特有的输出格式
                    if 'speed=' in line:
                        speed_match = re.search(r'speed=\s*([\d.]+)x', line)
                        if speed_match:
                            speed_factor = float(speed_match.group(1))
                            estimated_speed = (bitrate / 1e6) * speed_factor
                            speed_history.append(estimated_speed)
                            
                            # 估算下载量
                            current_time = time.time()
                            time_delta = current_time - last_time
                            if time_delta > 0:
                                downloaded += int((bitrate * speed_factor) * time_delta / 8)
                                last_time = current_time
                            
                            # 计算缓冲健康度
                            if bitrate > 0:
                                buffer_health = estimated_speed / (bitrate / 1e6)
                            
                            current_speed = estimated_speed
                except Exception as e:
                    logger.error(f"读取输出错误: {str(e)}")
                    break

        read_task = asyncio.create_task(read_output())
        
        try:
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, process.wait),
                timeout=10
            )
        except asyncio.TimeoutError:
            logger.warning(f"{protocol.upper()}测速超时: {url}")
        finally:
            try:
                process.kill()
            except:
                pass
            
            try:
                read_task.cancel()
                await asyncio.sleep(0.1)
            except:
                pass
            
            # 计算稳定性
            stability_score = 0.0
            if len(speed_history) > 1:
                avg_speed = sum(speed_history) / len(speed_history)
                variance = sum((s - avg_speed) ** 2 for s in speed_history) / len(speed_history)
                std_dev = variance ** 0.5
                stability_score = max(0, 1 - (std_dev / avg_speed)) if avg_speed > 0 else 0.0
            
            # 设置最终状态
            status = (current_speed > 0 and 
                     buffer_health > 0.6 and 
                     stability_score > 0.3)
            
            return {
                'download_speed': round(current_speed, 2),
                'speed_test_status': status,
                'speed_test_time': datetime.now().isoformat(),
                'downloaded_bytes': downloaded,
                'duration_seconds': round(time.time() - start_time, 2),
                'buffer_health': round(buffer_health, 2),
                'stability_score': round(stability_score, 2),
                'quality_score': round(min(1.0, current_speed / (bitrate / 1e6)) if bitrate > 0 else 0.0, 2)
            }
    except Exception as e:
        logger.error(f"测速失败: {url}, 错误: {str(e)}")
        return {
            'download_speed': 0.0,
            'speed_test_status': False,
            'speed_test_time': datetime.now().isoformat(),
            'downloaded_bytes': 0,
            'duration_seconds': 0.0,
            'buffer_health': 0.0,
            'stability_score': 0.0,
            'quality_score': 0.0
        }

async def test_http_download_speed(url: str, bitrate: int) -> dict:
    """
    使用ffmpeg测试流媒体下载速度
    返回:
        dict: 包含以下字段:
            - download_speed: 下载速度 (Mbps)
            - speed_test_status: 测试状态
            - speed_test_time: 测试时间
            - downloaded_bytes: 已下载字节数 (bytes)
            - duration_seconds: 测试持续时间 (秒)
            - buffer_health: 缓冲健康度 (0-1.0)
            - speed_stability: 速度稳定性 (0-1.0)
    """
    start_time = time.time()
    downloaded = 0
    speed = 0.0
    status = False
    
    # 新增：用于计算稳定性的速度历史记录
    speed_history = []
    buffer_health = 0.0
    
    try:
        import ffmpeg
        
        # 创建ffmpeg进程，设置超时和输出格式
        process = (
            ffmpeg
            .input(url, t=15)  # 增加测试时间到15秒以获取更准确的稳定性数据
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
        start_time = time.time()  # 记录测试开始时间
        last_size = 0  # 记录上次的大小，用于计算增量
        last_time = start_time  # 记录上次的时间

        async def read_output():
            nonlocal stderr_text, current_speed, downloaded, last_size, last_time, speed_history, buffer_health
            
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
                        # 改进正则表达式，允许N/A值
                        size_match = re.search(r'size=\s*([\d.]+|N/A)\s*kB', line)
                        time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                        speed_match = re.search(r'speed=\s*([\d.]+)x', line)
                        
                        current_time = time.time()
                        time_delta = current_time - last_time
                        
                        # 优先使用实际下载字节数
                        if size_match and size_match.group(1) != 'N/A':
                            current_size = int(float(size_match.group(1)) * 1024)  # kB转bytes
                            size_delta = current_size - last_size
                            
                            # 计算这个时间段的实时速度
                            if time_delta > 0 and size_delta > 0:
                                instant_speed = (size_delta * 8) / (time_delta * 1e6)  # bytes转Mbps
                                # 确保添加有效的速度值到历史记录
                                if instant_speed > 0:
                                    speed_history.append(instant_speed)
                                    logger.debug(f"添加速度历史记录: {instant_speed:.2f}Mbps, 当前历史记录数: {len(speed_history)}")
                                
                                # 更新最后的大小和时间
                                last_size = current_size
                                last_time = current_time
                            
                            downloaded = current_size
                        else:
                            # 备用方案：通过码率和速度倍率估算
                            if speed_match and bitrate > 0:
                                speed_factor = float(speed_match.group(1))
                                estimated_speed = (bitrate / 1e6) * speed_factor
                                # 也将估算的速度添加到历史记录
                                if estimated_speed > 0:
                                    speed_history.append(estimated_speed)
                                    logger.debug(f"添加估算速度到历史记录: {estimated_speed:.2f}Mbps, 当前历史记录数: {len(speed_history)}")
                                downloaded = int((bitrate * speed_factor) * (current_time - start_time) / 8)
                        
                        # 计算持续时间（即使没有size信息）
                        if time_match:
                            h, m, s = map(float, time_match.groups())
                            duration = h * 3600 + m * 60 + s
                        else:
                            duration = current_time - start_time
                        
                        # 最终速度计算逻辑
                        if duration > 0:
                            if downloaded > 0:  # 优先使用实际下载数据
                                current_speed = (downloaded * 8) / (duration * 1e6)  # bytes转Mbps
                            elif bitrate > 0 and speed_match:  # 备用方案
                                current_speed = bitrate / 1e6 * float(speed_match.group(1))
                        
                        # 计算缓冲健康度 - 下载速度与码率的比率
                        if bitrate > 0:
                            # 缓冲健康度 = 下载速度 / 所需码率
                            buffer_ratio = (current_speed * 1e6) / bitrate
                            # 修改为：允许超过1.0的值，表示有额外缓冲能力
                            buffer_health = buffer_ratio
                            logger.debug(f"缓冲健康度计算: 速度={current_speed:.2f}Mbps, 码率={bitrate/1e6:.2f}Mbps, 比率={buffer_ratio:.2f}")
                        
                        # 最低速度限制和日志记录
                        current_speed = max(current_speed, 0.1) if current_speed > 0 else 0.1
                        
                        # 调试日志包含数据来源信息
                        logger.debug(f"速度计算方式: {'实际数据' if size_match else '估算'} | "
                                    f"速度: {current_speed:.2f}Mbps 持续时间: {duration:.2f}s | "
                                    f"缓冲健康度: {buffer_health:.2f}")

                except Exception as e:
                    logger.error(f"读取输出错误: {str(e)}")
                    break

        # 启动输出读取任务
        read_task = asyncio.create_task(read_output())
        
        try:
            # 等待进程完成，最多15秒
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, process.wait),
                timeout=15
            )
        except asyncio.TimeoutError:
            logger.warning(f"测速超时: {url}")
        finally:
            # 确保进程被终止和清理
            try:
                process.kill()
            except:
                pass
            
            # 等待读取任务完成
            try:
                read_task.cancel()
                await asyncio.sleep(0.1)  # 给读取任务一点时间完成
            except:
                pass
            
            # 计算速度稳定性
            stability_score = 0.0
            logger.debug(f"计算稳定性，速度历史记录数: {len(speed_history)}")
            
            if len(speed_history) > 1:
                # 计算速度的标准差与平均值的比率，越小越稳定
                avg_speed = sum(speed_history) / len(speed_history)
                if avg_speed > 0:
                    variance = sum((s - avg_speed) ** 2 for s in speed_history) / len(speed_history)
                    std_dev = variance ** 0.5
                    # 稳定性评分 = 1 - (标准差/平均值)，限制在0-1范围内
                    # 如果标准差非常大，可能导致负值，所以使用max确保最小为0
                    coefficient = min(std_dev / avg_speed, 1.0)  # 限制系数最大为1
                    stability_score = max(0, 1 - coefficient)
                    logger.debug(f"稳定性计算: 平均速度={avg_speed:.2f}, 标准差={std_dev:.2f}, 系数={coefficient:.2f}, 稳定性评分={stability_score:.2f}")
            else:
                # 如果没有足够的历史记录，给一个默认的中等稳定性评分
                stability_score = 0.5
                logger.debug(f"历史记录不足，使用默认稳定性评分: {stability_score}")
            
            # 计算综合质量评分 (结合速度、缓冲健康度和稳定性)
            quality_score = 0.0
            if current_speed > 0:
                # 权重可以根据实际需求调整
                speed_weight = 0.4
                buffer_weight = 0.4
                stability_weight = 0.2
                
                # 速度评分 (相对于码率的比率，最高为1.0)
                speed_score = min(1.0, current_speed * 1e6 / (bitrate * 1.5)) if bitrate > 0 else 0.5
                
                # 缓冲健康度也需要限制在0-1范围内
                normalized_buffer_health = min(1.0, buffer_health)
                
                quality_score = (
                    speed_score * speed_weight + 
                    normalized_buffer_health * buffer_weight + 
                    stability_score * stability_weight
                )
                # 确保最终质量评分不超过1.0
                quality_score = min(1.0, quality_score)
            
            # 设置最终状态 - 改进判断标准
            # 不仅考虑速度，还考虑缓冲健康度和稳定性
            status = (current_speed > 0 and 
                     buffer_health > 0.6 and  # 缓冲至少要达到60%
                     stability_score > 0.3)   # 稳定性至少要达到30%
            
            speed = current_speed
            logger.info(f"测速完成: {url}, 速度: {speed:.2f}Mbps, 缓冲健康度: {buffer_health:.2f}, 稳定性: {stability_score:.2f}, 质量评分: {quality_score:.2f}")

    except Exception as e:
        logger.error(f"测速失败: {url}, {str(e)}")
        status = False
        speed = 0.0
        downloaded = 0
        buffer_health = 0.0
        stability_score = 0.0
        quality_score = 0.0

    return {
        'download_speed': round(speed, 2),  # 单位: Mbps
        'speed_test_status': status,
        'speed_test_time': datetime.now().isoformat(),
        'downloaded_bytes': downloaded,
        'duration_seconds': round(time.time() - start_time, 2),
        'buffer_health': round(buffer_health, 2),
        'stability_score': round(stability_score, 2),
        'quality_score': round(quality_score, 2)
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
                download_speed = ?, speed_test_status = ?, speed_test_time = ?,
                buffer_health = ?, stability_score = ?, quality_score = ?
               WHERE id = ?""",
            (status, speed, stream_info.get('video_codec'), 
             stream_info.get('audio_codec'), stream_info.get('resolution'),
             stream_info.get('bitrate'), stream_info.get('frame_rate'),
             stream_info.get('ping_time'), datetime.now().isoformat(),
             download_speed,  # 使用转换后的速度值
             stream_info.get('speed_test_status', False),
             stream_info.get('speed_test_time'),
             stream_info.get('buffer_health', 0.0),
             stream_info.get('stability_score', 0.0),
             stream_info.get('quality_score', 0.0),
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


# 添加失败计数器相关的常量和缓存
FAILURE_THRESHOLD = 4  # 允许的最大失败次数
FAILURE_WINDOW = 300  # 失败记录的有效期（秒）
FAILURE_DECAY_TIME = 1800  # 失败次数衰减时间（秒）

# 域名失败计数缓存
domain_failures: Dict[str, List[Tuple[datetime, str]]] = {}

def detect_stream_protocol(url: str) -> str:
    """检测流媒体协议类型"""
    url_lower = url.lower()
    if '.m3u8' in url_lower:
        return 'hls'
    elif url_lower.startswith('rtmp://'):
        return 'rtmp'
    elif url_lower.startswith('rtsp://'):
        return 'rtsp'
    elif url_lower.startswith('udp://'):
        return 'udp'
    else:
        return 'http'


async def probe_hls_stream(url: str) -> dict:
    """HLS流探测"""
    try:
        import m3u8
        from urllib.parse import urlparse
        
        # 解析主m3u8文件
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # 下载并解析m3u8文件
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                
                playlist = m3u8.loads(await resp.text())
                
                # 获取第一个有效片段URL进行测试
                if playlist.segments:
                    segment_url = urljoin(base_url, playlist.segments[0].uri)
                    return await probe_stream(segment_url)
                
        return {}
    except Exception as e:
        logger.error(f"HLS流探测失败: {url}, 错误: {str(e)}")
        return {}

async def probe_rtmp_stream(url: str) -> dict:
    """RTMP流探测"""
    try:
        # 使用FFmpeg的特殊参数探测RTMP
        import ffmpeg
        probe = ffmpeg.probe(url, timeout=5, rtmp_buffer=1000, rtmp_live='live')
        return probe if probe else {}
    except Exception as e:
        logger.error(f"RTMP流探测失败: {url}, 错误: {str(e)}")
        return {}

async def probe_rtsp_stream(url: str) -> dict:
    """RTSP流探测"""
    try:
        # 使用FFmpeg的特殊参数探测RTSP
        import ffmpeg
        probe = ffmpeg.probe(
            url, 
            timeout=5,
            rtsp_transport='tcp',  # 强制使用TCP传输
            rtsp_flags='prefer_tcp'
        )
        return probe if probe else {}
    except Exception as e:
        logger.error(f"RTSP流探测失败: {url}, 错误: {str(e)}")
        return {}
