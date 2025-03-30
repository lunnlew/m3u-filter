from fastapi import APIRouter
from datetime import datetime
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from database import get_db_connection
from models import BaseResponse
import logging
import asyncio
from collections import defaultdict
import time
import sqlite3  # 添加 sqlite3 导入
import re  # 添加 re 模块导入

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blocked-domains", tags=["blocked_domains"])

# 失败计数器相关的常量
FAILURE_THRESHOLD = 4  # 允许的最大失败次数
FAILURE_WINDOW = 300  # 失败记录的有效期（秒）
FAILURE_DECAY_TIME = 1800  # 失败次数衰减时间（秒）

# 域名失败计数缓存
domain_failures: Dict[str, List[Tuple[datetime, str]]] = {}

def get_domain_key(url: str) -> str:
    """从URL中提取域名/IP和端口作为键"""
    try:
        # 如果URL没有协议，默认添加http协议
        if not re.match(r'^[a-zA-Z]+://', url):
            url = f"http://{url}"

        parsed_url = urlparse(url)
        if parsed_url.netloc:
            return parsed_url.netloc
        else:
            logger.error(f"无法从URL中提取域名: {url}")
            return ""
    except Exception as e:
        logger.error(f"解析URL时发生错误: {str(e)}")
        return ""


# 添加内存缓存，减少数据库访问
domain_status_cache = {}
CACHE_CLEANUP_INTERVAL = 300  # 缓存清理间隔（秒）
last_cache_cleanup = time.time()

async def should_skip_domain(url: str) -> bool:
    """检查是否应该跳过该域名的测试"""
    global last_cache_cleanup
    domain_key = get_domain_key(url)
    now = datetime.now()
    
    # 清理过期缓存
    current_time = time.time()
    if current_time - last_cache_cleanup > CACHE_CLEANUP_INTERVAL:
        cleanup_expired_cache()
        last_cache_cleanup = current_time
    
    # 首先检查内存缓存
    if domain_key in domain_status_cache:
        cache_data = domain_status_cache[domain_key]
        if (now - cache_data['timestamp']).total_seconds() < FAILURE_DECAY_TIME:
            return cache_data['should_skip']
        else:
            del domain_status_cache[domain_key]
    
    # 检查内存中的临时失败记录
    if domain_key in domain_failures:
        domain_failures[domain_key] = [
            (t, e) for t, e in domain_failures[domain_key]
            if (now - t).total_seconds() < FAILURE_WINDOW
        ]
        if len(domain_failures[domain_key]) >= FAILURE_THRESHOLD:
            domain_status_cache[domain_key] = {
                'should_skip': True,
                'timestamp': now
            }
            return True
        elif not domain_failures[domain_key]:
            del domain_failures[domain_key]
    
    # 如果缓存中没有，则查询数据库
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT 1 FROM blocked_domains 
                WHERE domain = ? 
                AND datetime(last_failure_time) > datetime('now', ?)
                AND failure_count >= 10
            """, (domain_key, f'-{FAILURE_DECAY_TIME} seconds'))
            should_skip = bool(c.fetchone())
            
            # 更新缓存
            domain_status_cache[domain_key] = {
                'should_skip': should_skip,
                'timestamp': now
            }
            
            return should_skip
            
    except Exception as e:
        logger.error(f"检查域名黑名单失败: {str(e)}")
        return False

def cleanup_expired_cache():
    """清理过期的缓存数据"""
    now = datetime.now()
    expired_keys = [
        key for key, data in domain_status_cache.items()
        if (now - data['timestamp']).total_seconds() >= FAILURE_DECAY_TIME
    ]
    for key in expired_keys:
        del domain_status_cache[key]

# 添加新的缓存和批量更新相关的常量
UPDATE_BATCH_SIZE = 50  # 批量更新的大小
UPDATE_INTERVAL = 60  # 批量更新的时间间隔（秒）

# 添加更新缓存
pending_updates = defaultdict(lambda: {'count': 0, 'last_failure': None})
last_batch_update = time.time()

async def record_domain_failure(url: str, error: str) -> bool:
    """记录域名失败并返回是否应该跳过该域名"""
    global last_batch_update
    domain_key = get_domain_key(url)
    now = datetime.now()
    
    # 更新内存缓存
    if domain_key not in domain_failures:
        domain_failures[domain_key] = []
    domain_failures[domain_key].append((now, error))
    
    # 清理过期的失败记录并计算有效失败次数
    valid_failures = [
        (t, e) for t, e in domain_failures[domain_key]
        if (now - t).total_seconds() < FAILURE_WINDOW
    ]
    domain_failures[domain_key] = valid_failures
    recent_failures = len(valid_failures)
    
    # 更新待处理队列，使用实际的失败次数
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # 获取数据库中已存在的失败次数
            c.execute("""
                SELECT failure_count 
                FROM blocked_domains 
                WHERE domain = ? 
                AND datetime(last_failure_time) > datetime('now', ?)
            """, (domain_key, f'-{FAILURE_WINDOW} seconds'))
            result = c.fetchone()
            existing_failures = result[0] if result else 0
            
            # 计算总的有效失败次数
            total_failures = existing_failures + recent_failures
            
            pending_updates[domain_key] = {
                'count': total_failures,
                'last_failure': now,
                'errors': [e for _, e in valid_failures[-3:]]  # 保存最近3次错误信息
            }
    except Exception as e:
        logger.error(f"获取已存在的失败次数时出错: {str(e)}")
        # 如果查询失败，仅使用内存中的计数
        pending_updates[domain_key] = {
            'count': recent_failures,
            'last_failure': now,
            'errors': [e for _, e in valid_failures[-3:]]
        }
    
    # 检查是否需要执行批量更新
    current_time = time.time()
    should_update = (
        len(pending_updates) >= UPDATE_BATCH_SIZE or
        current_time - last_batch_update >= UPDATE_INTERVAL
    )
    
    if should_update:
        await batch_update_blocked_domains()
    
    return total_failures >= FAILURE_THRESHOLD

async def batch_update_blocked_domains():
    """批量更新域名黑名单"""
    global last_batch_update, pending_updates
    if not pending_updates:
        return
        
    max_retries = 5
    retry_delay = 2
    
    try:
        # 记录待更新的数据
        update_data = [
            (
                domain,
                data['count'],
                data['last_failure'].isoformat(),
                data['last_failure'].isoformat(),
                ','.join(data.get('errors', []))[:500]  # 限制错误信息长度
            )
            for domain, data in pending_updates.items()
        ]
        logger.info(f"准备更新 {len(update_data)} 条记录")
        
        # 将更新分批处理，每批10条减少单次事务量
        batch_size = 10
        success_count = 0
        
        for i in range(0, len(update_data), batch_size):
            batch = update_data[i:i + batch_size]
            
            for attempt in range(max_retries):
                try:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("BEGIN IMMEDIATE")
                        
                        try:
                            # 使用单条SQL语句批量更新
                            c.executemany("""
                                INSERT INTO blocked_domains 
                                    (domain, failure_count, last_failure_time, updated_at, last_errors)
                                VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT(domain) DO UPDATE SET
                                    failure_count = ?,
                                    last_failure_time = excluded.last_failure_time,
                                    updated_at = excluded.updated_at,
                                    last_errors = excluded.last_errors
                            """, [(d[0], d[1], d[2], d[3], d[4], d[1]) for d in batch])
                            
                            conn.commit()
                            success_count += len(batch)
                            logger.info(f"成功更新了第 {i//batch_size + 1} 批数据，共 {len(batch)} 条记录")
                            break  # 成功后跳出重试循环
                            
                        except Exception as e:
                            conn.rollback()
                            logger.error(f"执行批量更新时出错: {str(e)}")
                            raise
                            
                except sqlite3.OperationalError as e:
                    if "locked" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"数据库锁定，第{attempt+1}次重试批量更新")
                        await asyncio.sleep(retry_delay * (attempt + 1))
                    else:
                        logger.error(f"批量更新域名黑名单失败: {str(e)}")
                        break
                except Exception as e:
                    logger.error(f"批量更新域名黑名单时发生错误: {str(e)}")
                    break
        
        # 清空已成功更新的记录
        if success_count > 0:
            logger.info(f"总共成功更新了 {success_count} 条记录")
            pending_updates.clear()
            last_batch_update = time.time()
        else:
            logger.error("没有任何记录更新成功")
            
    except Exception as e:
        logger.error(f"准备更新数据时出错: {str(e)}")

@router.get("")
async def get_blocked_domains(page: int = 1, page_size: int = 10):
    """获取被阻止的域名列表（分页）"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # 获取总记录数
            c.execute("""
                SELECT COUNT(*) FROM blocked_domains
                WHERE datetime(last_failure_time) > datetime('now', ?)
            """, (f'-{FAILURE_DECAY_TIME} seconds',))
            total = c.fetchone()[0]
            
            # 获取分页数据
            c.execute("""
                SELECT domain, failure_count, last_failure_time, created_at, updated_at
                FROM blocked_domains
                WHERE datetime(last_failure_time) > datetime('now', ?)
                ORDER BY failure_count DESC
                LIMIT ? OFFSET ?
            """, (f'-{FAILURE_DECAY_TIME} seconds', page_size, (page - 1) * page_size))
            
            columns = [description[0] for description in c.description]
            domains = [dict(zip(columns, row)) for row in c.fetchall()]
            
            return BaseResponse.success(data={
                'items': domains,
                'total': total,
                'page': page,
                'page_size': page_size
            })
    except Exception as e:
        logger.error(f"获取域名黑名单失败: {str(e)}")
        return BaseResponse.error(message="获取域名黑名单失败", code=500)

@router.delete("/{domain}")
async def remove_blocked_domain(domain: str):
    """从黑名单中移除指定域名"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM blocked_domains WHERE domain = ?", (domain,))
            if c.rowcount == 0:
                return BaseResponse.error(message="域名不在黑名单中", code=404)
            conn.commit()
            
            if domain in domain_failures:
                del domain_failures[domain]
                
            return BaseResponse.success(message="域名已从黑名单中移除")
    except Exception as e:
        logger.error(f"移除域名黑名单失败: {str(e)}")
        return BaseResponse.error(message="移除域名黑名单失败", code=500)
