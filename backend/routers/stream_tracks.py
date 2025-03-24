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
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

async def test_stream_url(url: str) -> tuple[bool, float, dict]:
    try:
        # 检查ffmpeg是否可用
        try:
            import ffmpeg
        except ImportError:
            logger.error("ffmpeg-python库未安装，请先安装该库")
            return False, 0.0, {}

        start_time = datetime.now()
        logger.info(f"开始测试流媒体URL: {url}")

        try:
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
            probe = await probe_with_timeout(5)

            logger.error(f"ffmpeg探测成功: {url}, 解析结果: {probe}")

            # 计算探测耗时
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 添加ping测试
            ping_time = 0.0
            try: 
                ping_time = await ping_url(url)
            except Exception as e:
                logger.error(f"Ping测试时发生错误: {str(e)}")
                ping_time = 0.0

            # 初始化流媒体信息
            stream_info = {
                'video_codec': '',
                'audio_codec': '',
                'resolution': '',
                'bitrate': 0,
                'frame_rate': 0,
                'ping_time': ping_time  # 添加ping时间
            }

            # 验证probe结果是否为有效的JSON
            if not isinstance(probe, dict) or 'streams' not in probe:
                logger.error(f"无效的ffmpeg probe结果: {probe}")
                return False, 0.0, stream_info

            # 解析流信息
            for stream in probe.get('streams', []):
                if 'codec_type' in stream: 
                    if stream['codec_type'] == 'video':
                        # 视频流信息
                        stream_info['video_codec'] = stream.get('codec_name')
                        if stream.get('width') and stream.get('height'):
                            stream_info['resolution'] = f"{stream['width']}x{stream['height']}"
                        # 处理帧率
                        if stream.get('r_frame_rate'):
                            try:
                                num, den = map(int, stream['r_frame_rate'].split('/'))
                                if den != 0:
                                    stream_info['frame_rate'] = round(num / den, 2)
                            except (ValueError, ZeroDivisionError):
                                print(f"无效的帧率格式: {stream['r_frame_rate']}")
                                pass
                    elif stream['codec_type'] == 'audio':
                        # 音频流信息
                        stream_info['audio_codec'] = stream.get('codec_name')
                        # 处理比特率
                        if stream.get('bit_rate'):
                            try:
                                stream_info['bitrate'] = int(stream['bit_rate']) // 1000
                            except (ValueError, TypeError):
                                pass
                    else:
                        # 其他流类型
                        logger.warning(f"未知的流类型: {stream['codec_type']}")

                elif 'width' in stream and 'height' in stream:
                    # 视频流信息
                    stream_info['video_codec'] = stream.get('codec_name')
                    if stream.get('width') and stream.get('height'):
                        stream_info['resolution'] = f"{stream['width']}x{stream['height']}"

                    # 处理帧率
                    if stream.get('r_frame_rate'):
                        try:
                            num, den = map(int, stream['r_frame_rate'].split('/'))
                            if den != 0:
                                stream_info['frame_rate'] = round(num / den, 2)
                        except (ValueError, ZeroDivisionError):
                            pass

                elif stream['codec_name'] in ['aac', 'mp3', 'mp2', 'flac', 'opus', 'ac3', 'eac3', 'dts', 'dts-hd', 'truehd', 'ac-3', 'dts']:
                    # 音频流信息
                    stream_info['audio_codec'] = stream.get('codec_name')
                    # 处理比特率
                    if stream.get('bit_rate'):
                        try:
                            stream_info['bitrate'] = int(stream['bit_rate']) // 1000
                        except (ValueError, TypeError):
                            pass
                else:
                    # 其他流类型
                    logger.warning(f"未知的流类型: {stream['codec_name']}")

            logger.info(f"流媒体测试完成: {url}, 延迟: {duration}秒, 信息: {stream_info}")
            return True, duration, stream_info

        except ffmpeg.Error as fe:
            error_info = {
                'video_codec': None,
                'audio_codec': None,
                'resolution': None,
                'bitrate': None,
                'frame_rate': None,
                'stdout': getattr(fe, 'stdout', ''),
                'stderr': getattr(fe, 'stderr', str(fe))
            }
            logger.error(f"ffmpeg探测失败: {url}, 错误信息: {error_info['stderr']}")
            return False, 0.0, error_info

    except Exception as e:
        error_info = {
            'video_codec': None,
            'audio_codec': None,
            'resolution': None,
            'bitrate': None,
            'frame_rate': None,
            'stdout': '',
            'stderr': f"错误类型: {type(e).__name__}, 错误信息: {str(e)}"
        }
        logger.error(f"测试流媒体URL时发生错误: {url}, {error_info['stderr']}")
        return False, 0.0, error_info


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
                status, speed, stream_info = await test_stream_url(url)
                
                # 更新测试结果，包含ping时间
                c.execute(
                    "UPDATE stream_tracks SET test_status = ?, test_latency = ?, video_codec = ?, audio_codec = ?, resolution = ?, bitrate = ?, frame_rate = ?, ping_time = ?, last_test_time = ? WHERE id = ?",
                    (status, speed, stream_info.get('video_codec'), stream_info.get('audio_codec'), stream_info.get('resolution'), 
                     stream_info.get('bitrate'), stream_info.get('frame_rate'), stream_info.get('ping_time'), datetime.now().isoformat(), track_id)
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
        if test_status is not None:
            where_clause += " AND st.test_status =?"
            params.append(test_status)

        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM stream_tracks st {where_clause}"
        c.execute(count_query, params)
        total = c.fetchone()[0]

        # 计算分页参数
        offset = (page - 1) * page_size
        # 获取分页数据，包含source信息
        query = f"""SELECT st.*, ss.name as source_name, ss.url as source_url, ss.type as source_type 
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
        
        # 创建队列任务
        c.execute("""
            INSERT INTO stream_tasks (
                task_type, status, total_items
            ) VALUES (?, ?, ?)
        """, ('batch_test', 'pending', len(track_ids)))
        task_id = c.lastrowid
        conn.commit()
        
        # 启动后台处理
        import asyncio
        asyncio.create_task(process_task_queue(task_id, track_ids))
        
        return BaseResponse.success(
            data={"task_id": task_id},
            message=f"批量测试任务已创建，任务ID: {task_id}"
        )

async def process_task_queue(task_id: int, track_ids: list):
    logger.info(f"开始处理任务队列 {task_id}")
    try:
            # 初始化结果存储
            results = {}
            
            # 逐个处理任务
            for index, track_id in enumerate(track_ids, 1):
                # 每个任务使用独立连接
                with get_db_connection() as conn:
                    c = conn.cursor()
                    try:
                        await test_stream_track(track_id)
                        results[str(track_id)] = {
                            'status': 'success',
                            'timestamp': datetime.now().isoformat()
                        }
                    except Exception as e:
                        logger.error(f"任务处理失败 track_id={track_id}: {str(e)}")
                        results[str(track_id)] = {
                            'status': 'failed',
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    # 更新进度和结果
                    c.execute("""
                        UPDATE stream_tasks SET
                            processed_items = ?,
                            progress = ?,
                            result = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        index, 
                        index/len(track_ids),
                        str(results),
                        datetime.now().isoformat(),
                        task_id
                    ))
                    conn.commit()
            
            # 标记任务完成
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE stream_tasks SET
                        status = 'completed',
                        progress = 1.0,
                        result = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (str(results), datetime.now().isoformat(), task_id))
                conn.commit()
    except Exception as e:
        logger.error(f"任务队列处理失败 {task_id}: {str(e)}")
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE stream_tasks SET
                    status = 'failed',
                    result = ?,
                    updated_at = ?
                WHERE id = ?
            """, (f"System Error: {str(e)}", datetime.now().isoformat(), task_id))
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