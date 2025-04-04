import logging
from urllib.parse import urlparse
from ping3 import ping
from typing import Optional

logger = logging.getLogger(__name__)

async def ping_url(url: str) -> float:
    """
    测试URL的ping延迟时间
    参数:
        url: 要测试的URL
    返回:
        float: ping延迟时间(毫秒)，失败返回0.0
    """
    try:
        # 解析URL以提取域名或IP地址
        parsed_url = urlparse(url)
        host = parsed_url.hostname

        if not host:
            logger.error(f"无法解析URL: {url}")
            return 0.0

        # 使用ping3库测试域名或IP地址
        ping_time = ping(host, unit='ms')
        if ping_time is None:
            logger.error(f"Ping失败: 无法到达 {host}")
            return 0.0
        return ping_time
    except Exception as e:
        logger.error(f"Ping测试时发生错误: {str(e)}")
        return 0.0

async def check_ipv6_connectivity() -> bool:
    """
    检查系统是否支持IPv6连接
    返回:
        bool: 如果IPv6可用返回True，否则返回False
    """
    ipv6_test_hosts = [
        "2001:4860:4860::8888",  # Google DNS
        "2606:4700:4700::1111",  # Cloudflare DNS
        "2400:3200::1",          # Alibaba DNS
    ]
    
    for host in ipv6_test_hosts:
        try:
            ping_result = ping(host, timeout=2)
            if ping_result is not None and ping_result is not False:
                logger.info(f"IPv6连接测试成功: {host}")
                return True
        except Exception as e:
            logger.debug(f"IPv6测试失败 ({host}): {str(e)}")
            continue
    
    logger.warning("系统不支持IPv6连接")
    return False