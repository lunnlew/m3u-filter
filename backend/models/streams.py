from pydantic import BaseModel
from typing import Optional

class StreamSource(BaseModel):
    id: Optional[int] = None
    name: str
    url: str
    type: str  # m3u, m3u8, txt等
    last_update: Optional[str] = None
    active: bool = True
    sync_interval: Optional[int] = 6
    x_tvg_url: Optional[str] = None
    catchup: Optional[str] = None
    catchup_source: Optional[str] = None

class StreamTrack(BaseModel):
    id: Optional[int] = None
    name: str
    url: str
    group_title: Optional[str] = None
    source_id: int
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    catchup: Optional[str] = None
    catchup_source: Optional[str] = None
    last_test_time: Optional[str] = None  # 最后测试时间
    test_status: Optional[bool] = None  # 测试状态，True表示可用，False表示不可用
    test_latency: Optional[float] = None  # 测试延迟，单位为秒
    video_codec: Optional[str] = None  # 视频编码格式
    audio_codec: Optional[str] = None  # 音频编码格式
    resolution: Optional[str] = None  # 视频分辨率
    bitrate: Optional[int] = None  # 码率(kbps)
    frame_rate: Optional[float] = None  # 帧率