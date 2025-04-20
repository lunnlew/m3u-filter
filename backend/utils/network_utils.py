import logging
from urllib.parse import urlparse
from ping3 import ping
from typing import Optional
import socket
import re

logger = logging.getLogger(__name__)

# 添加全局变量存储 IPv6 支持状态
_ipv6_supported = None

async def check_ipv6_connectivity() -> bool:
    """
    检查系统是否支持IPv6连接
    返回:
        bool: 如果IPv6可用返回True，否则返回False
    """
    global _ipv6_supported
    
    # 如果已经检查过，直接返回缓存的结果
    if _ipv6_supported is not None:
        return _ipv6_supported
    
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
                _ipv6_supported = True
                return True
        except Exception as e:
            logger.info(f"IPv6测试失败 ({host}): {str(e)}")
            continue
    
    logger.debug("系统不支持IPv6连接")
    _ipv6_supported = False
    return False

def is_ipv6_address(host: str) -> bool:
    """
    检查主机名是否为IPv6地址
    """
    # IPv6地址格式的正则表达式
    ipv6_pattern = r'^(?:' + \
        r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|' + \
        r'(?:[0-9a-fA-F]{1,4}:){1,7}:|' + \
        r'(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|' + \
        r'(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|' + \
        r'(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|' + \
        r'(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|' + \
        r'(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|' + \
        r'[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|' + \
        r':(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|' + \
        r'fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|' + \
        r'::(?:ffff(?::0{1,4}){0,1}:){0,1}[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|' + \
        r'(?:[0-9a-fA-F]{1,4}:){1,4}:(?:[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})' + \
        r')$'
    
    return bool(re.match(ipv6_pattern, host))

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
            logger.debug(f"无法解析URL: {url}")
            return 0.0

        # 检查是否为IPv6地址
        if is_ipv6_address(host):
            # 如果是IPv6地址但系统不支持IPv6，直接返回失败
            if not await check_ipv6_connectivity():
                logger.debug(f"系统不支持IPv6，跳过测试: {host}")
                return 0.0

        # 使用ping3库测试域名或IP地址
        ping_time = ping(host, unit='ms')
        if ping_time is None:
            logger.debug(f"Ping失败: 无法到达 {host}")
            return 0.0
        return ping_time
    except Exception as e:
        logger.debug(f"Ping测试时发生错误: {str(e)}")
        return 0.0