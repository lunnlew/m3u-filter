import logging
from urllib.parse import urlparse
from ping3 import ping
from typing import Optional

logger = logging.getLogger(__name__)


def extract_frame_rate(stream: dict) -> float:
    """
    从视频流信息中提取帧率
    参数:
        stream: 包含视频流信息的字典
    返回:
        float: 帧率(帧/秒)，提取失败返回0.0
    """
    for rate_key in ['r_frame_rate', 'avg_frame_rate']:
        if stream.get(rate_key):
            try:
                num, den = map(int, stream[rate_key].split('/'))
                if den != 0:
                    return round(num / den, 2)
            except (ValueError, ZeroDivisionError):
                continue
    return 0.0


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
        'speed_test_time': None,
        'buffer_health': 0.0,  # 新增：缓冲健康度
        'stability_score': 0.0,  # 新增：稳定性评分
        'quality_score': 0.0,    # 新增：综合质量评分
    }


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

async def extract_stream_info(probe_result: dict, ping_time: float, speed_info: dict) -> dict:
    """Extract stream information from probe result"""
    stream_info = get_default_stream_info()
    stream_info.update({
        'ping_time': ping_time,
        'download_speed': speed_info.get('download_speed', 0.0),
        'speed_test_status': speed_info.get('speed_test_status', False),
        'speed_test_time': speed_info.get('speed_test_time'),
        'buffer_health': speed_info.get('buffer_health', 0.0),
        'stability_score': speed_info.get('stability_score', 0.0),
        'quality_score': speed_info.get('quality_score', 0.0)
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