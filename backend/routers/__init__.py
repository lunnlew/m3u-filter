# 路由模块初始化文件
from fastapi import APIRouter

from .epg_channels import router as epg_channels_router
from .epg_programs import router as epg_programs_router
from .epg_sources import router as epg_sources_router
from .proxy_config import router as proxy_config_router
from .default_channel_logos import router as default_channel_logos_router
from .static_files import router as static_files_router
from .site_config import router as site_config_router
from .stream_sources import router as stream_sources_router
from .stream_tracks import router as stream_tracks_router
from .filter_rules import router as filter_rules_router
from .filter_rule_sets import router as filter_rule_sets_router
from routers.health import router as health_router

api_router = APIRouter()

api_router.include_router(epg_channels_router, prefix="/api", tags=["epg-channels"])
api_router.include_router(epg_programs_router, prefix="/api", tags=["epg-programs"])
api_router.include_router(epg_sources_router, prefix="/api", tags=["epg-sources"])
api_router.include_router(proxy_config_router, prefix="/api", tags=["proxy-config"])
api_router.include_router(default_channel_logos_router, prefix="/api", tags=["channel-logos"])
api_router.include_router(site_config_router, prefix="/api", tags=["site-config"])
api_router.include_router(stream_sources_router, prefix="/api", tags=["stream-sources"])
api_router.include_router(stream_tracks_router, prefix="/api", tags=["stream-tracks"])
api_router.include_router(filter_rules_router, prefix="/api", tags=["filter-rules"])
api_router.include_router(filter_rule_sets_router, prefix="/api", tags=["filter-rule-sets"])
api_router.include_router(health_router, prefix="/api", tags=["health"])
api_router.include_router(static_files_router, tags=["static-files"])  # 移到最后