from pydantic import BaseModel
from typing import Optional

class EPGSource(BaseModel):
    id: Optional[int] = None
    name: str
    url: str
    last_update: Optional[str] = None
    active: bool = True
    sync_interval: Optional[int] = 6
    default_language: Optional[str] = 'en'

class EPGProgram(BaseModel):
    id: Optional[int] = None
    channel: str
    title: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    source_id: int

class EPGChannel(BaseModel):
    id: Optional[int] = None
    display_name: str
    language: str
    category: Optional[str] = None
    logo_url: Optional[str] = None
    local_logo_path: Optional[str] = None

class DefaultChannelLogo(BaseModel):
    id: Optional[int] = None
    channel_name: str
    logo_url: str
    priority: Optional[int] = 0  # 优先级，用于处理同名频道的情况