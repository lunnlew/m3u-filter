from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List, Optional, Tuple
from database import get_db_connection
from models import FilterRuleSet, FilterRuleSetMapping, RuleTree
import os
from m3u_generator import M3UGenerator
from models import BaseResponse
from datetime import datetime
from config import RESOURCE_ROOT
import json
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

from typing import List, Optional, Union, Literal

# 在文件顶部添加导入
from typing import Dict, Optional
from pydantic import BaseModel

class FilterRuleSetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    enabled: bool
    logic_type: Optional[str] = "AND"
    rules: List[dict]  # 修改为接收字典列表
    children: Optional[List[dict]] = None
    sync_interval: Optional[int] = None  # 新增字段，单位：分钟

from typing import List, Optional, Union, Literal

@router.get("/filter-rule-sets")
def get_filter_rule_sets(
    name: Optional[str] = None,
    enabled: Optional[bool] = None,
    logic_type: Optional[str] = None
):
    """获取所有规则集合，支持筛选"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 构建查询条件
        query = "SELECT id, name, description, enabled, logic_type, sync_interval FROM filter_rule_sets"
        conditions = []
        params = []
        
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        
        if enabled is not None:
            conditions.append("enabled = ?")
            params.append(1 if enabled else 0)
        
        if logic_type:
            conditions.append("logic_type = ?")
            params.append(logic_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        rule_sets = [dict(zip(columns, row)) for row in cursor.fetchall()]
        data = []
        for rule_set in rule_sets:
            # 获取子规则集合
            cursor.execute("""
                SELECT rs.id, rs.name, rs.description, rs.enabled, rs.sync_interval, rs.logic_type
                FROM filter_rule_sets rs
                INNER JOIN filter_rule_set_children rsc ON rs.id = rsc.child_set_id
                WHERE rsc.parent_set_id = ?
            """, (rule_set['id'],))
            children = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
            
            data.append(
                FilterRuleSetResponse(
                    id=rule_set['id'],
                    name=rule_set['name'],
                    description=rule_set['description'],
                    enabled=bool(rule_set['enabled']),
                    logic_type=rule_set['logic_type'],
                    sync_interval=rule_set['sync_interval'],
                    rules=_get_rules_for_set(cursor, rule_set['id']),
                    children=[{
                        'id': child['id'],
                        'name': child['name'],
                        'description': child['description'],
                        'enabled': bool(child['enabled']),
                        'logic_type': child['logic_type'],
                        'sync_interval': child['sync_interval'],
                        'rules': _get_rules_for_set(cursor, child['id'])
                    } for child in children]
                )
            )
        return BaseResponse.success(data=data)

def _get_rules_for_set(cursor, set_id: int) -> List[dict]:
    """获取规则集合中的所有规则"""
    cursor.execute("""
        SELECT fr.id, fr.name, fr.type, fr.pattern, fr.action, fr.priority, fr.enabled, fr.case_sensitive, fr.regex_mode 
        FROM filter_rules fr
        INNER JOIN filter_rule_set_mappings frsm ON fr.id = frsm.rule_id
        WHERE frsm.rule_set_id = ?
    """, (set_id,))
    columns = [column[0] for column in cursor.description]
    rules = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return [{
        'id': rule['id'],
        'name': rule['name'],
        'type': rule['type'],
        'pattern': rule['pattern'],
        'action': rule['action'],
        'priority': rule['priority'],
        'enabled': bool(rule['enabled']),
        'case_sensitive': bool(rule['case_sensitive']),
        'regex_mode': bool(rule['regex_mode'])
    } for rule in rules]

@router.post("/filter-rule-sets")
def create_filter_rule_set(rule_set: FilterRuleSet):
    """创建新的规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 检查名称是否重复
        cursor.execute("SELECT id FROM filter_rule_sets WHERE name = ?", (rule_set.name,))
        if cursor.fetchone():
            return BaseResponse.error(message="Rule set name already exists", code=400)
        
        cursor.execute(
            "INSERT INTO filter_rule_sets (name, description, enabled, logic_type, sync_interval) VALUES (?, ?, ?, ?, ?)",
            (rule_set.name, rule_set.description, rule_set.enabled, rule_set.logic_type, rule_set.sync_interval)
        )
        set_id = cursor.lastrowid
        
        # 添加子规则集合关系
        if rule_set.children:
            for child_id in rule_set.children:
                cursor.execute(
                    "INSERT INTO filter_rule_set_children (parent_set_id, child_set_id) VALUES (?, ?)",
                    (set_id, child_id)
                )
        
        conn.commit()
        return BaseResponse.success(data={"id": set_id})

@router.put("/filter-rule-sets/{set_id}")
def update_filter_rule_set(set_id: int, rule_set: FilterRuleSet):
    """更新规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 检查规则集合是否存在
        cursor.execute("SELECT id FROM filter_rule_sets WHERE id = ?", (set_id,))
        if not cursor.fetchone():
            return BaseResponse.error(message="Rule set not found", code=404)
        
        # 检查名称是否与其他规则集合重复
        cursor.execute("SELECT id FROM filter_rule_sets WHERE name = ? AND id != ?", (rule_set.name, set_id))
        if cursor.fetchone():
            return BaseResponse.error(message="Rule set name already exists", code=400)
        
        cursor.execute(
            "UPDATE filter_rule_sets SET name=?, description=?, enabled=?, logic_type=?, sync_interval=? WHERE id=?",
            (rule_set.name, rule_set.description, rule_set.enabled, rule_set.logic_type, rule_set.sync_interval, set_id)
        )
        
        # 更新子规则集合关系
        if rule_set.children:
            # 获取现有子规则集合
            cursor.execute("SELECT child_set_id FROM filter_rule_set_children WHERE parent_set_id=?", (set_id,))
            existing_children = set(row[0] for row in cursor.fetchall())
            new_children = set(rule_set.children)
            
            # 删除不再需要的子规则集合
            for child_id in existing_children - new_children:
                cursor.execute(
                    "DELETE FROM filter_rule_set_children WHERE parent_set_id=? AND child_set_id=?",
                    (set_id, child_id)
                )
            
            # 添加新的子规则集合
            for child_id in new_children - existing_children:
                cursor.execute(
                    "INSERT INTO filter_rule_set_children (parent_set_id, child_set_id) VALUES (?, ?)",
                    (set_id, child_id)
                )
        
        conn.commit()
        return BaseResponse.success()

@router.patch("/filter-rule-sets/{set_id}/toggle")
def toggle_filter_rule_set(set_id: int):
    """切换规则集合的启用状态"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT enabled FROM filter_rule_sets WHERE id = ?", (set_id,))
        result = cursor.fetchone()
        if not result:
            return BaseResponse.error(message="Rule set not found", code=404)
        
        new_status = not bool(result[0])
        cursor.execute(
            "UPDATE filter_rule_sets SET enabled = ? WHERE id = ?",
            (new_status, set_id)
        )
        conn.commit()
        return BaseResponse.success(data={"enabled": new_status})

@router.delete("/filter-rule-sets/{set_id}")
def delete_filter_rule_set(set_id: int):
    """删除规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 首先删除规则集合与规则的关联关系
        cursor.execute("DELETE FROM filter_rule_set_mappings WHERE rule_set_id=?", (set_id,))
        # 删除子规则集合关系
        cursor.execute("DELETE FROM filter_rule_set_children WHERE parent_set_id=? OR child_set_id=?", (set_id, set_id))
        # 然后删除规则集合
        cursor.execute("DELETE FROM filter_rule_sets WHERE id=?", (set_id,))
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Rule set not found", code=404)
        conn.commit()
        return BaseResponse.success()

@router.post("/filter-rule-sets/{parent_set_id}/rule-sets/{child_set_id}")
def add_child_set(parent_set_id: int, child_set_id: int):
    """向规则集合中添加子规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 检查父子集合是否存在
        cursor.execute("SELECT id FROM filter_rule_sets WHERE id IN (?, ?)", (parent_set_id, child_set_id))
        existing = cursor.fetchall()
        if len(existing) != 2:
            return BaseResponse.error(message="Parent or child set not found", code=404)
        
        # 检查是否会产生循环依赖
        cursor.execute("""
            WITH RECURSIVE ancestors(id) AS (
                SELECT parent_set_id 
                FROM filter_rule_set_children 
                WHERE child_set_id = ?
                UNION
                SELECT c.parent_set_id 
                FROM filter_rule_set_children c, ancestors a
                WHERE c.child_set_id = a.id
            )
            SELECT id FROM ancestors WHERE id = ?
        """, (parent_set_id, child_set_id))
        if cursor.fetchone():
            return BaseResponse.error(message="Adding child would create cyclic dependency", code=400)
        
        # 检查是否已存在关联
        cursor.execute("""
            SELECT 1 FROM filter_rule_set_children 
            WHERE parent_set_id = ? AND child_set_id = ?
        """, (parent_set_id, child_set_id))
        if cursor.fetchone():
            return BaseResponse.error(message="Child set already exists", code=400)
        
        cursor.execute("""
            INSERT INTO filter_rule_set_children (parent_set_id, child_set_id)
            VALUES (?, ?)
        """, (parent_set_id, child_set_id))
        
        conn.commit()
        return BaseResponse.success()

@router.post("/filter-rule-sets/{set_id}/rules/{rule_id}")
def add_rule_to_set(set_id: int, rule_id: int):
    """向规则集合中添加规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 检查规则集合和规则是否存在
        cursor.execute("SELECT id FROM filter_rule_sets WHERE id=?", (set_id,))
        if not cursor.fetchone():
            return BaseResponse.error(message="Rule set not found", code=404)
        
        cursor.execute("SELECT id FROM filter_rules WHERE id=?", (rule_id,))
        if not cursor.fetchone():
            return BaseResponse.error(message="Rule not found", code=404)
        
        # 检查规则是否已经在集合中
        cursor.execute(
            "SELECT 1 FROM filter_rule_set_mappings WHERE rule_set_id=? AND rule_id=?",
            (set_id, rule_id)
        )
        if cursor.fetchone():
            return BaseResponse.error(message="Rule already exists in set", code=400)
        
        # 添加关联关系
        cursor.execute(
            "INSERT INTO filter_rule_set_mappings (rule_set_id, rule_id) VALUES (?, ?)",
            (set_id, rule_id)
        )
        conn.commit()
        return BaseResponse.success()

@router.delete("/filter-rule-sets/{set_id}/rules/{rule_id}")
def remove_rule_from_set(set_id: int, rule_id: int):
    """从规则集合中移除规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM filter_rule_set_mappings WHERE rule_set_id=? AND rule_id=?",
            (set_id, rule_id)
        )
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Rule not found in set", code=404)
        conn.commit()
        return BaseResponse.success()

@router.delete("/filter-rule-sets/{parent_set_id}/rule-sets/{child_set_id}")
def remove_child_set(parent_set_id: int, child_set_id: int):
    """从规则集合中移除子规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM filter_rule_set_children 
            WHERE parent_set_id=? AND child_set_id=?
            """,
            (parent_set_id, child_set_id)
        )
        if cursor.rowcount == 0:
            return BaseResponse.error(message="RuleSet not found", code=404)
        conn.commit()
        return BaseResponse.success()

def _get_filtered_channels(set_id: int, conn) -> Tuple[List[dict], List[dict[str, str]], Dict[str, List[str]]]:
    ""
    """
    获取过滤后的频道列表（公共函数）
    返回处理后的频道列表，包括分组映射和排序后的结果
    """
    cursor = conn.cursor()
    # 获取规则集合
    cursor.execute("SELECT id, name, enabled, logic_type FROM filter_rule_sets WHERE id = ?", (set_id,))
    rule_set = cursor.fetchone()
    if not rule_set:
        raise HTTPException(status_code=404, detail="规则集合不存在")
    
    if not rule_set[2]:  # enabled
        raise HTTPException(status_code=400, detail="Rule set is disabled")
    
    # 获取所有频道
    cursor.execute("""
        SELECT
            stream_tracks.id,
            stream_tracks.name as display_name,
            stream_tracks.url as stream_url,
            stream_tracks.tvg_name,
            stream_tracks.tvg_logo,
            stream_tracks.tvg_language,
            stream_tracks.group_title,
            stream_tracks.test_status,
            stream_tracks.catchup,
            stream_tracks.catchup_source,
            stream_tracks.download_speed,
            stream_tracks.resolution,
            stream_tracks.bitrate,
            stream_tracks.quality_score,
            epg_channels.channel_id,
            epg_channels.language,
            epg_channels.category,
            COALESCE(
                epg_channels.local_logo_path,
                epg_channels.logo_url,
                (SELECT local_logo_path FROM default_channel_logos 
                WHERE channel_name = stream_tracks.name 
                ORDER BY priority DESC LIMIT 1),
                (SELECT logo_url FROM default_channel_logos 
                WHERE channel_name = stream_tracks.name 
                ORDER BY priority DESC LIMIT 1)
            ) as logo_url,
            epg_sources.name AS source_name,
            epg_sources.id AS source_id
        FROM stream_tracks
        LEFT JOIN epg_channels ON stream_tracks.name = epg_channels.display_name
        LEFT JOIN epg_sources ON epg_channels.source_id = epg_sources.id
    """)
    columns = [description[0] for description in cursor.description]
    channels = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # 获取规则树
    rule_tree = RuleTree()
    rule_tree.build_from_rule_set(set_id, conn)

    # 使用规则树过滤频道
    filtered_channels = rule_tree.filter_channels(channels)
    
    # 获取分组映射和模板
    cursor.execute("""
        SELECT channel_name, custom_group, display_name 
        FROM (
            SELECT channel_name, custom_group, display_name, 1 as priority
            FROM group_mappings
            WHERE rule_set_id = ?
            UNION ALL
            SELECT gmt.channel_name, gmt.custom_group, NULL as display_name, 2 as priority
            FROM group_mapping_template_items gmt
            INNER JOIN group_mapping_templates t ON gmt.template_id = t.id
            WHERE t.rule_set_id = ?
            UNION ALL
            SELECT channel_name, custom_group, display_name, 3 as priority
            FROM group_mappings
            WHERE rule_set_id IS NULL
        ) combined
        GROUP BY channel_name
        HAVING priority = MIN(priority)
    """, (set_id, set_id))
    group_mappings = {row[0]: {'custom_group': row[1], 'display_name': row[2]} for row in cursor.fetchall()}
    
    # 应用分组映射和自定义显示名称
    for channel in filtered_channels:
        if channel['display_name'] in group_mappings:
            mapping = group_mappings[channel['display_name']]
            channel['group_title'] = mapping['custom_group']
            if mapping['display_name']:
                channel['display_name'] = mapping['display_name']
            
    # 按分组和频道名称对频道进行分组
    grouped_channels = {}
    for channel in filtered_channels:
        group = channel.get('group_title', 'Unknown')
        name = channel.get('display_name', '')
        key = (group, name)
        if key not in grouped_channels:
            grouped_channels[key] = []
        grouped_channels[key].append(channel)

    # 对每个分组下的同名频道按质量评分、清晰度和下载速度排序并只保留前2个
    final_channels = []
    for (group, name), channels in grouped_channels.items():
        sorted_channels = sorted(
            channels, 
            key=lambda x: (
                float(x.get('quality_score', 0) or 0),
                _get_resolution_score(x.get('resolution', '')),
                float(x.get('download_speed', 0) or 0)
            ), 
            reverse=True
        )
        for channel in sorted_channels[:2]:
            channel['group_title'] = group
            final_channels.append(channel)

    cursor.execute("""
        SELECT name, group_orders
        FROM sort_templates
    """)
    sort_templates_raw = cursor.fetchall()
    sort_templates = {}

    for template_name, group_orders in sort_templates_raw:
        try:
            # 解析JSON格式的group_orders
            orders = json.loads(group_orders)
            # 合并到sort_templates中
            for group_name, channels in orders.items():
                if group_name not in sort_templates:
                    sort_templates[group_name] = []
                sort_templates[group_name].extend(channels)
        except json.JSONDecodeError:
            logger.debug(f"Invalid JSON format in sort template: {template_name}")
            continue
    
    return rule_set, final_channels, sort_templates

@router.post("/filter-rule-sets/{set_id}/generate-m3u")
async def generate_m3u_file(
    set_id: int,
    sort_by: str = 'display_name',
    group_order: List[str] = []
):
    """根据规则集合生成M3U文件"""
    with get_db_connection() as conn:
        rule_set, final_channels, sort_templates = _get_filtered_channels(set_id, conn)
        
        # 使用规则集合名称作为文件名
        filename = f"{rule_set[1]}"
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        # 使用M3UGenerator生成m3u文件
        header_info = {
            "generated_at": datetime.now().isoformat(),
            "provider": "M3U Filter"
        }

        generator = M3UGenerator()
        m3u_content, filename = generator.generate_m3u(
            final_channels,
            [filename], 
            header_info,
            sort_by=sort_by,
            group_order=group_order,
            sort_templates=sort_templates  # 使用合并后的排序模板
        )
        
        # 保存到m3u文件夹
        m3u_dir = Path(RESOURCE_ROOT) / 'm3u'
        # 确保静态文件目录存在
        if not m3u_dir.exists():
            m3u_dir.mkdir(parents=True)

        file_path = m3u_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        return BaseResponse.success({"url_path": f"/m3u/{filename}"})

# 添加辅助函数用于计算分辨率评分
def _get_resolution_score(resolution: str) -> int:
    """
    根据分辨率返回评分，分辨率越高分数越高
    """
    if not resolution:
        return 0
        
    try:
        # 尝试解析分辨率格式，如 "1920x1080"
        if 'x' in resolution:
            width, height = map(int, resolution.lower().split('x'))
            return width * height  # 使用像素总数作为评分
        
        # 处理常见分辨率标识
        resolution = resolution.upper()
        if '4K' in resolution or '2160P' in resolution:
            return 3840 * 2160
        elif '1440P' in resolution or '2K' in resolution:
            return 2560 * 1440
        elif '1080P' in resolution or 'FHD' in resolution:
            return 1920 * 1080
        elif '720P' in resolution or 'HD' in resolution:
            return 1280 * 720
        elif '576P' in resolution or 'SD' in resolution:
            return 720 * 576
        elif '480P' in resolution:
            return 720 * 480
        elif '360P' in resolution:
            return 480 * 360
        else:
            # 尝试从字符串中提取数字
            import re
            numbers = re.findall(r'\d+', resolution)
            if numbers:
                # 假设最大的数字可能是高度
                return int(max(numbers, key=int)) * 16/9  # 估算宽度
    except Exception as e:
        logger.debug(f"解析分辨率失败: {resolution}, 错误: {str(e)}")
    
    return 0  # 默认返回0

@router.post("/filter-rule-sets/{set_id}/generate-txt")
async def generate_txt_file(
    set_id: int,
    sort_by: str = 'display_name',
    group_order: List[str] = []
):
    """根据规则集合生成TXT风格文件"""
    with get_db_connection() as conn:
        rule_set, final_channels, sort_templates = _get_filtered_channels(set_id, conn)
        
        # 使用规则集合名称作为文件名
        filename = f"{rule_set[1]}"
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))

        # 使用M3UGenerator生成TXT文件
        generator = M3UGenerator()
        txt_content, filename = generator.generate_txt(final_channels, [filename], sort_by, group_order, sort_templates)
        
        # 保存到m3u文件夹
        m3u_dir = Path(RESOURCE_ROOT) / 'm3u'
        if not m3u_dir.exists():
            m3u_dir.mkdir(parents=True)

        file_path = m3u_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return BaseResponse.success({"url_path": f"/m3u/{filename}"})

@router.post("/filter-rule-sets/{set_id}/test-rules")
async def test_rules_in_set(
    set_id: int,
    test_status: Optional[bool] = None,
    last_test_before: Optional[str] = None,
    min_failure_count: Optional[int] = None,
    max_failure_count: Optional[int] = 5,
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 首先验证规则集合是否存在且启用
            cursor.execute(
                "SELECT enabled FROM filter_rule_sets WHERE id = ?",
                (set_id,)
            )
            result = cursor.fetchone()
            if not result:
                return BaseResponse.error(message="规则集合不存在", code=404)
            if not result[0]:
                return BaseResponse.error(message="规则集合未启用", code=400)

            # 获取所有频道，跳过1小时内测试过的
            cursor.execute("""
                SELECT id, name, url, group_title, test_status, 
                       last_test_time, probe_failure_count
                FROM stream_tracks
                WHERE last_test_time IS NULL 
                   OR datetime(last_test_time) <= datetime('now', '-1 hour')
            """)
            columns = [column[0] for column in cursor.description]
            channels = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # 使用规则树过滤频道，但排除测试相关规则
            rule_tree = RuleTree()
            rule_tree.build_from_rule_set_without_test(set_id, conn)  # 使用新方法
            filtered_channels = rule_tree.filter_channels(channels)

            # 应用测试相关的过滤条件
            test_channels = []
            for channel in filtered_channels:
                if (test_status is None or channel.get('test_status') == test_status) and \
                   (last_test_before is None or 
                    channel.get('last_test_time') is None or 
                    channel.get('last_test_time') < last_test_before) and \
                   (min_failure_count is None or 
                    (channel.get('probe_failure_count') or 0) >= min_failure_count) and \
                   (max_failure_count is None or 
                    (channel.get('probe_failure_count') or 0) < max_failure_count):
                    test_channels.append(channel)

            if not test_channels:
                return BaseResponse.error(message="没有找到符合条件的频道", code=404)
            
            # 创建测试任务
            cursor.execute("""
                INSERT INTO stream_tasks (
                    task_type, status, total_items
                ) VALUES (?, ?, ?)
            """, ('rule_test', 'pending', len(test_channels)))
            task_id = cursor.lastrowid
            conn.commit()
            
            # 启动后台处理任务
            from .stream_tracks import process_batch_tasks
            asyncio.create_task(process_batch_tasks(task_id, [c['id'] for c in test_channels]))
            
            return BaseResponse.success(
                data={
                    "task_id": task_id,
                    "total_tracks": len(test_channels)
                },
                message=f"规则测试任务已创建，任务ID: {task_id}"
            )
            
    except Exception as e:
        logger.debug(f"创建规则测试任务失败: {str(e)}")
        return BaseResponse.error(message=f"创建测试任务失败: {str(e)}", code=500)