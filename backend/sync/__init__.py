from datetime import datetime
import sqlite3
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from bs4.element import Tag, NavigableString, PageElement
# 下载台标
from utils import download_and_save_logo
import aiohttp
from database import get_db_connection
import sqlite3
from typing import List, Dict
import re
import io
import zipfile
import gzip
from config import DATABASE_FILE
from routers.blocked_domains import should_skip_domain

def get_proxy_config():
    """获取代理配置"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM proxy_config LIMIT 1")
        columns = [description[0] for description in c.description]
        proxy_config_row = c.fetchone()
        return dict(zip(columns, proxy_config_row)) if proxy_config_row else None
    finally:
        conn.close()

def get_proxy_settings():
    """根据代理配置生成requests使用的代理设置"""
    proxy_config = get_proxy_config()
    if not proxy_config or not proxy_config['enabled']:
        return None
    
    proxy_type = proxy_config['proxy_type']
    host = proxy_config['host']
    port = proxy_config['port']
    username = proxy_config['username']
    password = proxy_config['password']
    
    auth = f"{username}:{password}@" if username and password else ""
    proxy_url = f"{proxy_type}://{auth}{host}:{port}"
    
    return {
        "http": proxy_url,
        "https": proxy_url
    }

async def sync_epg_source(source_id: int):
    """同步单个EPG数据源"""
    print(f"[同步EPG] 开始同步源ID: {source_id}")
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    c = conn.cursor()
    
    try:
        # 检查源是否存在并获取默认语言
        c.execute("SELECT url, default_language FROM epg_sources WHERE id = ?", (source_id,))
        result = c.fetchone()
        if not result:
            raise ValueError("EPG源不存在")
        
        url, default_language = result
        print(f"[同步EPG] 获取到源URL: {url}")
        proxies = get_proxy_settings()
        if proxies:
            print(f"[同步EPG] 使用代理设置: {proxies}")
        
        # 获取EPG XML数据
        print("[同步EPG] 开始下载EPG数据...")
        response = requests.get(url, proxies=proxies)
        if response.status_code != 200:
            raise Exception(f"获取EPG数据失败: HTTP {response.status_code}")
        
        content = response.content
        content_type = response.headers.get('Content-Type', '').lower()
        print(f"[同步EPG] 成功获取数据，Content-Type: {content_type}")
        
        # 处理gz格式的响应
        if 'application/gzip' in content_type or 'application/x-gzip' in content_type or url.lower().endswith('.gz'):
            print("[同步EPG] 检测到GZ压缩格式，开始解压...")
            content = gzip.decompress(content)
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                content = content.decode('latin1')
            print("[同步EPG] GZ解压完成")
        
        # 处理zip格式的响应
        elif 'application/zip' in content_type or url.lower().endswith('.zip'):
            print("[同步EPG] 检测到ZIP压缩格式，开始解压...")
            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                # 查找zip文件中的xml文件
                xml_files = [f for f in zip_file.namelist() if f.lower().endswith('.xml')]
                if not xml_files:
                    raise Exception("ZIP文件中未找到XML文件")
                print(f"[同步EPG] 在ZIP中找到XML文件: {xml_files[0]}")
                # 使用第一个找到的xml文件
                content = zip_file.read(xml_files[0])
            print("[同步EPG] ZIP解压完成")

        print("[同步EPG] 开始解析XML数据...")
        root = ET.fromstring(content)
        
        # 清除该源的旧数据
        print("[同步EPG] 清除旧数据...")
        c.execute("DELETE FROM epg_channels WHERE source_id = ?", (source_id,))
        c.execute("DELETE FROM epg_programs WHERE source_id = ?", (source_id,))
        
        # 解析并收集频道信息
        print("[同步EPG] 开始解析频道信息...")
        channels_data = []
        channel_count = 0
        for channel in root.findall('.//channel'):
            channel_count += 1
            channel_id = channel.get('id', '')
            display_name_elem = channel.find('.//display-name')
            display_name = display_name_elem.text.strip() if display_name_elem is not None and display_name_elem.text else ''
            language = display_name_elem.get('lang', default_language) if display_name_elem is not None else default_language
            
            icon_elem = channel.find('.//icon')
            logo_url = icon_elem.get('src', None) if icon_elem is not None else None
            
            category_elem = channel.find('.//category')
            category = category_elem.text.strip() if category_elem is not None and category_elem.text else None
            
            local_logo_path = None
            if logo_url:
                try:
                    print(f"[同步EPG] 下载频道 {display_name} 的台标...")
                    local_logo_path = await download_and_save_logo(logo_url, display_name)
                except Exception as e:
                    print(f"[同步EPG] 下载台标失败: {str(e)}")
            
            channels_data.append((
                channel_id, display_name, language, category, logo_url, source_id, local_logo_path
            ))
        
        print(f"[同步EPG] 解析到 {channel_count} 个频道")
        
        # 批量插入频道数据
        if channels_data:
            print("[同步EPG] 开始插入频道数据...")
            c.executemany(
                "INSERT OR IGNORE INTO epg_channels (channel_id, display_name, language, category, logo_url, source_id, local_logo_path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                channels_data
            )
        
        # 解析并收集节目信息
        print("[同步EPG] 开始解析节目信息...")
        programs_data = []
        program_count = 0
        for programme in root.findall('.//programme'):
            program_count += 1
            channel_id = programme.get('channel', '')
            start_time = programme.get('start', '')
            end_time = programme.get('stop', '')
            title_elem = programme.find('title')
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
            language = title_elem.get('lang', default_language) if title_elem is not None else default_language
            desc_elem = programme.find('desc')
            desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else None
            
            category_elem = programme.find('category')
            category = category_elem.text.strip() if category_elem is not None and category_elem.text else None
            
            programs_data.append((
                channel_id, title, start_time, end_time, desc, language, category, source_id
            ))
        
        print(f"[同步EPG] 解析到 {program_count} 个节目")
        
        # 批量插入节目数据
        if programs_data:
            print("[同步EPG] 开始插入节目数据...")
            c.executemany(
                "INSERT OR IGNORE INTO epg_programs (channel_id, title, start_time, end_time, description, language, category, source_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                programs_data
            )
        
        # 更新同步时间
        print("[同步EPG] 更新同步时间...")
        c.execute(
            "UPDATE epg_sources SET last_update = ? WHERE id = ?",
            (datetime.now().isoformat(), source_id)
        )
        
        conn.commit()
        print(f"[同步EPG] 同步完成，源ID: {source_id}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[同步EPG] 同步失败: {str(e)}")
        raise e
    finally:
        conn.close()

async def sync_all_active_sources():
    """同步所有激活的EPG数据源"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    c = conn.cursor()
    
    try:
        c.execute("SELECT id FROM epg_sources WHERE active = 1")
        source_ids = [row[0] for row in c.fetchall()]
        
        results = []
        for source_id in source_ids:
            try:
                await sync_epg_source(source_id)
                results.append({"source_id": source_id, "success": True})
            except Exception as e:
                results.append({"source_id": source_id, "success": False, "error": str(e)})
        
        return results
    finally:
        conn.close()

def extract_table_data(url: str, selector: str) -> List[Dict[str, str]]:
    """从指定网站URL中提取表格数据
    
    Args:
        url: 目标网页URL
        selector: CSS选择器，用于定位目标表格
        
    Returns:
        list: 包含表格数据的列表，每个元素是一个字典，表示表格的一行数据。
              对于包含链接的单元格，会额外包含'xxx_href'字段存储链接地址。
        
    Raises:
        Exception: 当网络请求失败或解析出错时抛出异常
    """
    try:
        # 获取代理设置
        proxies = get_proxy_settings()
        
        # 发送HTTP请求获取页面内容
        response = requests.get(url, proxies=proxies)
        if response.status_code != 200:
            raise Exception(f"获取页面数据失败: HTTP {response.status_code}")
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找目标表格
        table = soup.select_one(selector)
        if not table:
            raise Exception(f"未找到匹配的表格元素: {selector}")
        
        # 提取表头
        headers = []
        for th in table.find_all(['th', 'td']):
            headers.append(th.get_text(strip=True))
        
        # 提取表格数据
        data = []
        for row in table.find_all('tr')[1:]:  # 跳过表头行
            row_data = {}
            cells = row.find_all(['td', 'th'])
            for i, cell in enumerate(cells):
                if i < len(headers):
                    # 提取单元格文本内容
                    row_data[headers[i]] = cell.get_text(strip=True)
                    # 检查是否存在链接
                    link = cell.find('a')
                    if link and link.get('href'):
                        row_data[f"{headers[i]}_href"] = link.get('href')
            if row_data:
                data.append(row_data)
        
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求错误: {str(e)}")
    except Exception as e:
        raise Exception(f"解析表格数据失败: {str(e)}")

async def sync_stream_source(source_id: int):
    """同步指定直播源的数据"""
    print(f"[同步直播源] 开始同步源ID: {source_id}")
    # 获取直播源信息
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM stream_sources WHERE id = ?", (source_id,))
        source = c.fetchone()
        if not source:
            raise ValueError("直播源不存在")
        
        # 将结果转换为字典
        columns = [description[0] for description in c.description]
        source = dict(zip(columns, source))
        print(f"[同步直播源] 获取到源信息: {source['name']} ({source['url']})")
    
    try:
        # 获取代理设置
        proxies = get_proxy_settings()
        if proxies:
            print("[同步直播源] 使用代理设置获取内容")
        
        # 获取直播源内容
        async with aiohttp.ClientSession() as session:
            # 设置代理
            if proxies:
                proxy_url = proxies.get('http') or proxies.get('https')
                print(f"[同步直播源] 通过代理 {proxy_url} 获取内容")
                async with session.get(source['url'], proxy=proxy_url) as response:
                    if response.status != 200:
                        raise Exception(f"获取直播源数据失败: HTTP {response.status}")
                    content = await response.text()
            else:
                print("[同步直播源] 直接获取内容")
                async with session.get(source['url']) as response:
                    if response.status != 200:
                        raise Exception(f"获取直播源数据失败: HTTP {response.status}")
                    content = await response.text()

        print("[同步直播源] 成功获取内容，开始解析")
        tvg_channel = {
            'x_tvg_url': source.get('x_tvg_url'),
            'catchup': source.get('catchup'),
            'catchup_source': source.get('catchup_source')
        }     
        # 根据文件类型解析内容
        if source['url'].lower().endswith('.m3u') or source['url'].lower().endswith('.m3u8') or content.strip().startswith('#EXTM3U') or source['type'] == 'm3u':
            print("[同步直播源] 解析M3U格式内容")
            channels, tvg_channel = parse_m3u_content(content)
        else:
            # 处理txt格式
            print("[同步直播源] 解析TXT格式内容")
            channels = parse_txt_content(content)
        
        print(f"[同步直播源] 解析完成，获取到 {len(channels)} 个频道")
        
        # 过滤黑名单域名
        filtered_channels = []
        for channel in channels:
            if not await should_skip_domain(channel['url']):
                filtered_channels.append(channel)
            else:
                print(f"[同步直播源] 跳过黑名单域名: {channel['url']}")
        
        print(f"[同步直播源] 过滤后剩余 {len(filtered_channels)} 个频道")
        
        # 更新数据库
        with get_db_connection() as conn:
            c = conn.cursor()
            try:
                print("[同步直播源] 开始更新数据库")
                # 先删除该源的旧数据
                c.execute("DELETE FROM stream_tracks WHERE source_id = ?", (source_id,))
                
                # 插入过滤后的频道数据
                for channel in filtered_channels:
                    c.execute(
                        "INSERT INTO stream_tracks (source_id, name, url, group_title, tvg_id, tvg_name, tvg_logo, tvg_language, route_info, catchup, catchup_source) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            source_id,
                            channel.get('name'),
                            channel.get('url'),
                            channel.get('group-title'),
                            channel.get('tvg-id'),
                            channel.get('tvg-name'),
                            channel.get('tvg-logo'),
                            channel.get('tvg-language'),
                            channel.get('route_info'),
                            tvg_channel.get('catchup'),
                            tvg_channel.get('catchup_source')
                        )
                    )

                # 更新同步时间
                c.execute(
                    "UPDATE stream_sources SET last_update = CURRENT_TIMESTAMP, x_tvg_url = ?, catchup = ?, catchup_source = ? WHERE id = ?",
                    (tvg_channel.get('x_tvg_url', ''), tvg_channel.get('catchup', ''), tvg_channel.get('catchup_source', ''), source_id)
                )

                # 如果有epg地址，则检查是否已存在，不存在才加入epg表
                if tvg_channel.get('x_tvg_url'):
                    print(f"[同步直播源] 发现EPG地址: {tvg_channel['x_tvg_url']}")
                    # 处理可能存在的多个EPG地址（以逗号分隔）
                    epg_urls = [url.strip() for url in tvg_channel['x_tvg_url'].split(',') if url.strip()]
                    
                    for epg_url in epg_urls:
                        c.execute("SELECT COUNT(*) FROM epg_sources WHERE url = ?", (epg_url,))
                        if c.fetchone()[0] == 0:
                            print(f"[同步直播源] 添加新的EPG源: {epg_url}")
                            c.execute(
                                "INSERT INTO epg_sources (name, url, active, sync_interval, default_language) VALUES (?, ?, ?, ?, ?)",
                                (f"来自直播订阅{source['name']}", epg_url, True, 6, 'zh')
                            )
                            epg_source_id = c.lastrowid
                            from scheduler import update_source_schedule
                            update_source_schedule(epg_source_id)

                conn.commit()
                print("[同步直播源] 数据库更新完成")
            except Exception as e:
                conn.rollback()
                print(f"[同步直播源] 数据库更新失败: {str(e)}")
                raise Exception(f"更新数据库失败: {str(e)}")
        
        print(f"[同步直播源] 同步完成，源ID: {source_id}")
        return filtered_channels
                
    except aiohttp.ClientError as e:
        error_msg = f"网络请求失败: {str(e)}"
        print(f"[同步直播源] {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"同步失败: {str(e)}"
        print(f"[同步直播源] {error_msg}")
        raise

def parse_m3u_content(content: str) -> tuple[List[Dict[str, str]], Dict[str, str]]:
    """解析m3u格式内容"""
    if not content.strip().startswith('#EXTM3U'):
        raise ValueError("无效的M3U格式")
    
    channels = []
    current_channel = {}
    tvg_channel = {}
    
    # 解析#EXTM3U行中的全局属性
    first_line = content.splitlines()[0].strip()
    for attr in ['x-tvg-url', 'catchup', 'catchup-source']:
        attr_match = re.search(f'{attr}="([^"]+)"', first_line)
        if attr_match:
            tvg_channel[attr.replace('-', '_')] = attr_match.group(1)
    
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#EXTINF:'):
            # 解析频道信息
            # 先提取扩展属性，避免属性值干扰频道名称的提取
            for attr in ['group-title', 'tvg-id', 'tvg-name', 'tvg-logo', 'tvg-language']:
                attr_match = re.search(f'{attr}="([^"]+)"', line)
                if attr_match:
                    current_channel[attr] = attr_match.group(1)
            
            # 提取频道名称 - 使用更灵活的匹配方式
            name_match = re.search(r'#EXTINF:-?\d+(?:[^,]*,(.+))?$', line)
            if name_match and name_match.group(1):
                # 清理可能存在的属性标签
                name = name_match.group(1)
                # 移除任何剩余的属性标签
                name = re.sub(r'[a-zA-Z0-9-]+="[^"]*"', '', name).strip()
                current_channel['name'] = name
                
        elif not line.startswith('#'):
            current_channel['url'] = line
            # 这是频道URL
            if 'name' in current_channel:
                channels.append(current_channel.copy())
                current_channel = {}
            elif 'tvg-name' in current_channel:
                current_channel['name'] = current_channel['tvg-name']
                channels.append(current_channel.copy())
                current_channel = {}
            elif 'group-title' in current_channel:
                current_channel['name'] = current_channel['group-title']
                channels.append(current_channel.copy())
                current_channel = {}

    return (channels, tvg_channel)

def parse_txt_content(content: str) -> List[Dict[str, str]]:
    """解析txt格式内容
    支持以下格式：
    1. 频道名,播放地址
    2. 频道名,分组,播放地址
    3. 单行播放地址（使用URL最后一段作为频道名）
    4. 分组名,#genre#
       频道名,播放地址
    5. 频道名,播放地址$线路信息
    """
    channels = []
    current_group = None
    # 标准化换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    # 移除 BOM
    content = content.strip('\ufeff')
    
    # 打印更详细的调试信息
    lines = content.splitlines()
    print(f"[解析TXT] 总行数: {len(lines)}")
    print(f"[解析TXT] 原始内容长度: {len(content)}")
    print(f"[解析TXT] 非空行数: {len([line for line in lines if line.strip()])}")
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split(',')
        
        # 检查是否是分组标记行
        if len(parts) == 2 and parts[1].strip() == '#genre#':
            current_group = parts[0].strip()
            continue
        
        channel = {}
        
        if len(parts) == 1:  # 仅包含URL
            url = parts[0].strip()
            # 处理可能存在的$后缀
            url_parts = url.split('$', 1)
            url = url_parts[0]
            route_info = url_parts[1] if len(url_parts) > 1 else None
            # 从URL中提取名称（使用最后一段，去除扩展名）
            name = url.split('/')[-1].split('?')[0].rsplit('.', 1)[0]
            channel = {
                'name': name,
                'url': url,
                'route_info': route_info
            }
        elif len(parts) >= 2:  # 名称,URL格式 或 名称,分组,URL格式
            name = parts[0].strip()
            if len(parts) >= 3:  # 名称,分组,URL格式
                channel['group-title'] = parts[1].strip()
                url_part = parts[2].strip()
            else:  # 名称,URL格式
                url_part = parts[1].strip()
            
            # 处理URL中的$后缀
            url_parts = url_part.split('$', 1)
            url = url_parts[0]
            route_info = url_parts[1] if len(url_parts) > 1 else None
            
            channel.update({
                'name': name,
                'url': url,
                'route_info': route_info
            })
        
        if channel and channel.get('url'):
            # 如果当前有分组，且channel中没有group-title，则添加分组信息
            if current_group and 'group-title' not in channel:
                channel['group-title'] = current_group
            channels.append(channel)
    
    return channels